"""
Cost monitoring service for the Interview Evaluator application.
Tracks LLM API usage, costs, and provides forecasting.
"""

import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from app.services.langsmith.client import langsmith_service
from app.services.monitoring import get_monitoring_service

# Configure logger
logger = logging.getLogger(__name__)

# Constants for cost calculation
MODEL_COSTS = {
    "gpt-4": {
        "input": 0.03 / 1000,  # $0.03 per 1K input tokens
        "output": 0.06 / 1000,  # $0.06 per 1K output tokens
    },
    "gpt-4-turbo": {
        "input": 0.01 / 1000,  # $0.01 per 1K input tokens
        "output": 0.03 / 1000,  # $0.03 per 1K output tokens
    },
    "gpt-3.5-turbo": {
        "input": 0.001 / 1000,  # $0.001 per 1K input tokens
        "output": 0.002 / 1000,  # $0.002 per 1K output tokens
    },
    "claude-3-opus": {
        "input": 0.015 / 1000,  # $0.015 per 1K input tokens
        "output": 0.075 / 1000,  # $0.075 per 1K output tokens
    },
    "claude-3-sonnet": {
        "input": 0.003 / 1000,  # $0.003 per 1K input tokens
        "output": 0.015 / 1000,  # $0.015 per 1K output tokens
    },
    "default": {
        "input": 0.003 / 1000,  # Default cost per 1K input tokens
        "output": 0.015 / 1000,  # Default cost per 1K output tokens
    }
}

# LLM cost budget threshold (default)
DEFAULT_BUDGET_THRESHOLD = 100.0  # USD


class DailyCostRecord(BaseModel):
    """Model for a daily cost record."""
    date: datetime
    input_tokens: int
    output_tokens: int
    cost: float
    model_breakdown: Dict[str, float]


class CostMonitoringService:
    """Service for monitoring LLM API costs."""

    def __init__(self):
        """Initialize the cost monitoring service."""
        self.daily_costs: List[DailyCostRecord] = []
        self.budget_threshold = float(os.getenv("LLM_BUDGET_THRESHOLD", DEFAULT_BUDGET_THRESHOLD))
        self.alert_threshold_percentage = 0.8  # Alert at 80% of budget
        self.last_sync = None
        
    async def sync_with_langsmith(self):
        """Sync cost data with LangSmith."""
        try:
            # Get LangSmith client
            if not langsmith_service or not langsmith_service.is_connected():
                logger.warning("LangSmith client not available for cost monitoring")
                return
            
            # Set the sync window
            if self.last_sync:
                start_time = self.last_sync
            else:
                # Start from 30 days ago if no previous sync
                start_time = datetime.now() - timedelta(days=30)
                
            end_time = datetime.now()
            
            # Get run data from LangSmith
            runs = await langsmith_service.list_runs(
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat()
            )
            
            if not runs:
                logger.info("No new runs found in LangSmith")
                self.last_sync = end_time
                return
            
            # Group runs by date and model
            daily_stats = {}
            
            for run in runs:
                # Skip runs with no token info
                if "input_tokens" not in run or "output_tokens" not in run:
                    continue
                
                # Extract date and model info
                run_datetime = datetime.fromisoformat(run.get("start_time"))
                run_date = run_datetime.date().isoformat()
                model = run.get("extra", {}).get("model_name", "default")
                
                # Initialize date entry if not exists
                if run_date not in daily_stats:
                    daily_stats[run_date] = {
                        "total_input_tokens": 0,
                        "total_output_tokens": 0,
                        "total_cost": 0.0,
                        "model_breakdown": {}
                    }
                
                # Add token counts
                input_tokens = run.get("input_tokens", 0)
                output_tokens = run.get("output_tokens", 0)
                
                daily_stats[run_date]["total_input_tokens"] += input_tokens
                daily_stats[run_date]["total_output_tokens"] += output_tokens
                
                # Calculate cost for this run
                model_cost = MODEL_COSTS.get(model, MODEL_COSTS["default"])
                run_cost = (input_tokens * model_cost["input"]) + (output_tokens * model_cost["output"])
                
                daily_stats[run_date]["total_cost"] += run_cost
                
                # Add to model breakdown
                if model not in daily_stats[run_date]["model_breakdown"]:
                    daily_stats[run_date]["model_breakdown"][model] = 0.0
                
                daily_stats[run_date]["model_breakdown"][model] += run_cost
            
            # Update daily costs
            for date_str, stats in daily_stats.items():
                date = datetime.fromisoformat(date_str)
                
                # Check if we already have a record for this date
                existing_record = next((r for r in self.daily_costs if r.date.date().isoformat() == date_str), None)
                
                if existing_record:
                    # Update existing record
                    existing_record.input_tokens += stats["total_input_tokens"]
                    existing_record.output_tokens += stats["total_output_tokens"]
                    existing_record.cost += stats["total_cost"]
                    
                    # Update model breakdown
                    for model, cost in stats["model_breakdown"].items():
                        if model in existing_record.model_breakdown:
                            existing_record.model_breakdown[model] += cost
                        else:
                            existing_record.model_breakdown[model] = cost
                else:
                    # Create new record
                    record = DailyCostRecord(
                        date=date,
                        input_tokens=stats["total_input_tokens"],
                        output_tokens=stats["total_output_tokens"],
                        cost=stats["total_cost"],
                        model_breakdown=stats["model_breakdown"]
                    )
                    self.daily_costs.append(record)
            
            # Update last sync time
            self.last_sync = end_time
            
            # Check if we're approaching budget threshold
            await self.check_budget_threshold()
            
            # Update monitoring metrics
            await self.update_monitoring_metrics()
            
            logger.info(f"Cost data synced from LangSmith ({len(runs)} runs)")
            
        except Exception as e:
            logger.error(f"Error syncing cost data from LangSmith: {str(e)}")
            raise
    
    async def check_budget_threshold(self):
        """Check if we're approaching the budget threshold."""
        # Calculate current month's total
        today = datetime.now()
        month_start = datetime(today.year, today.month, 1)
        current_month_costs = [
            record for record in self.daily_costs 
            if record.date >= month_start
        ]
        
        if not current_month_costs:
            return
        
        # Calculate total cost for current month
        monthly_cost = sum(record.cost for record in current_month_costs)
        
        # Check if we're approaching the threshold
        if monthly_cost >= (self.budget_threshold * self.alert_threshold_percentage):
            logger.warning(f"Approaching LLM budget threshold: ${monthly_cost:.2f} / ${self.budget_threshold:.2f}")
            
            # Create alert
            monitoring_service = get_monitoring_service()
            await monitoring_service.create_alert(
                level="WARNING" if monthly_cost < self.budget_threshold else "ERROR",
                message=f"LLM cost warning: Monthly spending of ${monthly_cost:.2f} is {(monthly_cost / self.budget_threshold) * 100:.1f}% of budget (${self.budget_threshold:.2f})",
                source="cost_monitoring"
            )
    
    async def update_monitoring_metrics(self):
        """Update monitoring metrics with cost data."""
        monitoring_service = get_monitoring_service()
        
        # Calculate current month's total
        today = datetime.now()
        month_start = datetime(today.year, today.month, 1)
        current_month_costs = [
            record for record in self.daily_costs 
            if record.date >= month_start
        ]
        
        if not current_month_costs:
            return
        
        # Calculate totals
        monthly_cost = sum(record.cost for record in current_month_costs)
        monthly_input_tokens = sum(record.input_tokens for record in current_month_costs)
        monthly_output_tokens = sum(record.output_tokens for record in current_month_costs)
        total_tokens = monthly_input_tokens + monthly_output_tokens
        
        # Update metrics
        await monitoring_service.record_metric("llm_monthly_cost", monthly_cost)
        await monitoring_service.record_metric("llm_monthly_tokens", total_tokens)
        await monitoring_service.record_metric("llm_monthly_input_tokens", monthly_input_tokens)
        await monitoring_service.record_metric("llm_monthly_output_tokens", monthly_output_tokens)
        await monitoring_service.record_metric("llm_budget_percentage", (monthly_cost / self.budget_threshold) * 100)
    
    async def get_daily_costs(self, days: int = 30) -> List[Dict[str, Any]]:
        """Get daily costs for the specified number of days."""
        # Ensure data is up to date
        await self.sync_with_langsmith()
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # Filter records by date
        filtered_records = [
            record for record in self.daily_costs 
            if record.date >= start_date and record.date <= end_date
        ]
        
        # Sort by date (newest first)
        filtered_records.sort(key=lambda r: r.date, reverse=True)
        
        # Convert to dictionary format
        result = [
            {
                "date": record.date.date().isoformat(),
                "input_tokens": record.input_tokens,
                "output_tokens": record.output_tokens,
                "total_tokens": record.input_tokens + record.output_tokens,
                "cost": record.cost,
                "model_breakdown": record.model_breakdown
            }
            for record in filtered_records
        ]
        
        return result
    
    async def get_monthly_summary(self) -> Dict[str, Any]:
        """Get summary of current month's costs."""
        # Ensure data is up to date
        await self.sync_with_langsmith()
        
        # Calculate current month's range
        today = datetime.now()
        month_start = datetime(today.year, today.month, 1)
        
        # Filter records for current month
        current_month_costs = [
            record for record in self.daily_costs 
            if record.date >= month_start
        ]
        
        # Calculate totals
        monthly_cost = sum(record.cost for record in current_month_costs)
        monthly_input_tokens = sum(record.input_tokens for record in current_month_costs)
        monthly_output_tokens = sum(record.output_tokens for record in current_month_costs)
        total_tokens = monthly_input_tokens + monthly_output_tokens
        
        # Calculate model breakdown
        model_breakdown = {}
        for record in current_month_costs:
            for model, cost in record.model_breakdown.items():
                if model in model_breakdown:
                    model_breakdown[model] += cost
                else:
                    model_breakdown[model] = cost
        
        # Calculate daily average
        days_elapsed = (today - month_start).days + 1
        daily_average_cost = monthly_cost / days_elapsed if days_elapsed > 0 else 0
        
        # Project remainder of month
        days_remaining = (
            (month_start.replace(month=month_start.month % 12 + 1, day=1) if month_start.month < 12 
             else month_start.replace(year=month_start.year + 1, month=1, day=1)) - today
        ).days
        projected_additional_cost = daily_average_cost * days_remaining
        projected_total_cost = monthly_cost + projected_additional_cost
        
        # Calculate budget metrics
        budget_used_percentage = (monthly_cost / self.budget_threshold) * 100 if self.budget_threshold > 0 else 0
        projected_budget_percentage = (projected_total_cost / self.budget_threshold) * 100 if self.budget_threshold > 0 else 0
        
        return {
            "current_month": today.strftime("%B %Y"),
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "monthly_cost_to_date": monthly_cost,
            "monthly_input_tokens": monthly_input_tokens,
            "monthly_output_tokens": monthly_output_tokens,
            "monthly_total_tokens": total_tokens,
            "daily_average_cost": daily_average_cost,
            "projected_additional_cost": projected_additional_cost,
            "projected_total_cost": projected_total_cost,
            "budget_threshold": self.budget_threshold,
            "budget_used_percentage": budget_used_percentage,
            "projected_budget_percentage": projected_budget_percentage,
            "model_breakdown": model_breakdown
        }
    
    async def set_budget_threshold(self, new_threshold: float) -> Dict[str, Any]:
        """Set a new budget threshold."""
        if new_threshold <= 0:
            raise HTTPException(status_code=400, detail="Budget threshold must be positive")
        
        # Set the new threshold
        self.budget_threshold = new_threshold
        
        # Check if we're now over the threshold
        await self.check_budget_threshold()
        
        return {
            "budget_threshold": self.budget_threshold,
            "alert_threshold_percentage": self.alert_threshold_percentage,
            "alert_threshold": self.budget_threshold * self.alert_threshold_percentage
        }
    
    async def get_cost_projection(self) -> Dict[str, Any]:
        """Get cost projection for the next 30 days."""
        # Ensure data is up to date
        await self.sync_with_langsmith()
        
        # Calculate recent daily averages
        today = datetime.now()
        last_7_days = today - timedelta(days=7)
        
        recent_records = [
            record for record in self.daily_costs 
            if record.date >= last_7_days
        ]
        
        if not recent_records:
            return {
                "current_usage_tokens": 0,
                "current_cost": 0.0,
                "projected_30day_tokens": 0,
                "projected_30day_cost": 0.0,
                "burn_rate_per_day": 0.0,
                "days_to_budget": float('inf') if self.budget_threshold > 0 else 0
            }
        
        # Calculate totals for recent period
        recent_cost = sum(record.cost for record in recent_records)
        recent_tokens = sum(record.input_tokens + record.output_tokens for record in recent_records)
        
        # Calculate daily averages
        days_count = min(7, len(recent_records))
        daily_cost_average = recent_cost / days_count
        daily_token_average = recent_tokens / days_count
        
        # Project for next 30 days
        projected_30day_cost = daily_cost_average * 30
        projected_30day_tokens = daily_token_average * 30
        
        # Calculate days until budget exhausted
        days_to_budget = self.budget_threshold / daily_cost_average if daily_cost_average > 0 else float('inf')
        
        return {
            "current_usage_tokens": recent_tokens,
            "current_cost": recent_cost,
            "projected_30day_tokens": projected_30day_tokens,
            "projected_30day_cost": projected_30day_cost,
            "burn_rate_per_day": daily_cost_average,
            "days_to_budget": days_to_budget
        }


# Create a global instance
cost_monitoring_service = None

def get_cost_monitoring_service() -> CostMonitoringService:
    """Get or create the cost monitoring service singleton."""
    global cost_monitoring_service
    if cost_monitoring_service is None:
        cost_monitoring_service = CostMonitoringService()
    return cost_monitoring_service