"""
Monitoring service for the interview evaluator application.
Handles system monitoring, metrics collection, and alerting.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

import httpx
import sentry_sdk
from fastapi import HTTPException
from pydantic import BaseModel

from app.services.langsmith.client import LangSmithService
from app.services.supabase_client import SupabaseService

# Configure logger
logger = logging.getLogger(__name__)

# Constants
ALERT_LEVELS = {
    "INFO": 0,
    "WARNING": 1,
    "ERROR": 2,
    "CRITICAL": 3
}


class MetricValue(BaseModel):
    """Model for a metric value with timestamp."""
    timestamp: datetime
    value: Union[int, float, str, bool]


class Metric(BaseModel):
    """Model for a metric with name, description, and values."""
    name: str
    description: str
    unit: Optional[str] = None
    values: List[MetricValue]


class Alert(BaseModel):
    """Model for an alert."""
    id: str
    timestamp: datetime
    level: str
    message: str
    source: str
    acknowledged: bool = False
    resolved: bool = False
    resolved_at: Optional[datetime] = None


class MonitoringService:
    """Service for system monitoring, metrics collection, and alerting."""

    def __init__(self, 
                 supabase_client: Optional[SupabaseService] = None,
                 langsmith_client: Optional[LangSmithService] = None):
        """Initialize the monitoring service."""
        self.supabase_client = supabase_client
        self.langsmith_client = langsmith_client
        self.alerts: List[Alert] = []
        
        # Default metrics
        self.metrics: Dict[str, Metric] = {
            "api_requests": Metric(
                name="api_requests",
                description="Number of API requests",
                unit="count",
                values=[]
            ),
            "evaluation_count": Metric(
                name="evaluation_count",
                description="Number of evaluations performed",
                unit="count",
                values=[]
            ),
            "average_evaluation_time": Metric(
                name="average_evaluation_time",
                description="Average time to complete an evaluation",
                unit="seconds",
                values=[]
            ),
            "error_count": Metric(
                name="error_count",
                description="Number of errors",
                unit="count",
                values=[]
            ),
            "llm_tokens_used": Metric(
                name="llm_tokens_used",
                description="Number of LLM tokens used",
                unit="count",
                values=[]
            ),
            "llm_cost": Metric(
                name="llm_cost",
                description="Estimated cost of LLM usage",
                unit="USD",
                values=[]
            ),
        }
        
        # Initialize webhook endpoints for alerting
        self.webhook_endpoints = []
        if os.getenv("ALERT_WEBHOOK"):
            self.webhook_endpoints.append(os.getenv("ALERT_WEBHOOK"))

    async def record_metric(self, name: str, value: Union[int, float, str, bool]):
        """Record a metric value."""
        if name not in self.metrics:
            self.metrics[name] = Metric(
                name=name,
                description=f"Custom metric: {name}",
                values=[]
            )
            
        metric_value = MetricValue(
            timestamp=datetime.now(),
            value=value
        )
        self.metrics[name].values.append(metric_value)
        
        # Truncate to last 1000 values to prevent memory issues
        if len(self.metrics[name].values) > 1000:
            self.metrics[name].values = self.metrics[name].values[-1000:]
        
        # If we have Supabase, store the metric
        if self.supabase_client:
            try:
                await self.supabase_client.from_("metrics").insert({
                    "name": name,
                    "value": json.dumps(value) if not isinstance(value, (int, float, bool)) else value,
                    "recorded_at": metric_value.timestamp.isoformat()
                }).execute()
            except Exception as e:
                logger.error(f"Failed to store metric in Supabase: {e}")
                # Report to Sentry if available
                sentry_sdk.capture_exception(e)
    
    async def get_metrics(self, name: Optional[str] = None, 
                         time_range: Optional[timedelta] = None) -> Dict[str, Metric]:
        """Get metrics, optionally filtered by name and time range."""
        now = datetime.now()
        result = {}
        
        if name:
            if name not in self.metrics:
                raise HTTPException(status_code=404, detail=f"Metric '{name}' not found")
            
            metric = self.metrics[name]
            if time_range:
                filtered_values = [v for v in metric.values 
                                  if now - v.timestamp <= time_range]
                result[name] = Metric(
                    name=metric.name,
                    description=metric.description,
                    unit=metric.unit,
                    values=filtered_values
                )
            else:
                result[name] = metric
        else:
            for metric_name, metric in self.metrics.items():
                if time_range:
                    filtered_values = [v for v in metric.values 
                                      if now - v.timestamp <= time_range]
                    result[metric_name] = Metric(
                        name=metric.name,
                        description=metric.description,
                        unit=metric.unit,
                        values=filtered_values
                    )
                else:
                    result[metric_name] = metric
                    
        return result
    
    async def create_alert(self, level: str, message: str, source: str) -> Alert:
        """Create a new alert."""
        if level not in ALERT_LEVELS:
            raise ValueError(f"Invalid alert level: {level}")
        
        alert_id = f"alert_{len(self.alerts) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        alert = Alert(
            id=alert_id,
            timestamp=datetime.now(),
            level=level,
            message=message,
            source=source
        )
        
        self.alerts.append(alert)
        
        # Log the alert
        log_method = getattr(logger, level.lower(), logger.info)
        log_method(f"ALERT [{level}] from {source}: {message}")
        
        # Report to Sentry if critical or error
        if level in ["ERROR", "CRITICAL"]:
            sentry_sdk.capture_message(
                f"Alert [{level}] from {source}: {message}",
                level=level.lower()
            )
        
        # Send webhook notifications for critical alerts
        if level == "CRITICAL" and self.webhook_endpoints:
            await self._send_alert_notifications(alert)
            
        return alert
    
    async def _send_alert_notifications(self, alert: Alert):
        """Send alert notifications to configured endpoints."""
        for endpoint in self.webhook_endpoints:
            try:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        endpoint,
                        json={
                            "text": f"🚨 *CRITICAL ALERT*: {alert.message}",
                            "attachments": [
                                {
                                    "color": "#FF0000",
                                    "fields": [
                                        {"title": "Source", "value": alert.source, "short": True},
                                        {"title": "Time", "value": alert.timestamp.isoformat(), "short": True}
                                    ]
                                }
                            ]
                        }
                    )
            except Exception as e:
                logger.error(f"Failed to send alert notification: {e}")
                sentry_sdk.capture_exception(e)
    
    async def get_alerts(self, 
                        level: Optional[str] = None, 
                        resolved: Optional[bool] = None,
                        time_range: Optional[timedelta] = None) -> List[Alert]:
        """Get alerts, optionally filtered by level, resolved status, and time range."""
        now = datetime.now()
        filtered_alerts = self.alerts
        
        if level:
            if level not in ALERT_LEVELS:
                raise ValueError(f"Invalid alert level: {level}")
            filtered_alerts = [a for a in filtered_alerts if a.level == level]
            
        if resolved is not None:
            filtered_alerts = [a for a in filtered_alerts if a.resolved == resolved]
            
        if time_range:
            filtered_alerts = [a for a in filtered_alerts 
                              if now - a.timestamp <= time_range]
                              
        return filtered_alerts
    
    async def acknowledge_alert(self, alert_id: str) -> Alert:
        """Acknowledge an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.acknowledged = True
                return alert
                
        raise HTTPException(status_code=404, detail=f"Alert with ID '{alert_id}' not found")
    
    async def resolve_alert(self, alert_id: str) -> Alert:
        """Resolve an alert."""
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                return alert
                
        raise HTTPException(status_code=404, detail=f"Alert with ID '{alert_id}' not found")
    
    async def get_langsmith_metrics(self) -> Dict:
        """Get metrics from LangSmith."""
        if not self.langsmith_client:
            logger.warning("LangSmith client not available for metrics collection")
            return {"error": "LangSmith client not available"}
        
        try:
            # Get run statistics
            runs = await self.langsmith_client.list_runs(
                start_time=(datetime.now() - timedelta(days=7)).isoformat()
            )
            
            # Calculate metrics
            total_runs = len(runs)
            successful_runs = len([r for r in runs if r.get("error") is None])
            failed_runs = total_runs - successful_runs
            
            # Calculate average latency
            latencies = [
                r.get("end_time", 0) - r.get("start_time", 0) 
                for r in runs 
                if r.get("end_time") and r.get("start_time")
            ]
            avg_latency = sum(latencies) / len(latencies) if latencies else 0
            
            # Calculate token usage and cost (estimated)
            input_tokens = sum(r.get("input_tokens", 0) for r in runs)
            output_tokens = sum(r.get("output_tokens", 0) for r in runs)
            total_tokens = input_tokens + output_tokens
            
            # Estimate cost (simplified)
            estimated_cost = (input_tokens * 0.0000005) + (output_tokens * 0.0000015)
            
            # Update local metrics
            await self.record_metric("llm_tokens_used", total_tokens)
            await self.record_metric("llm_cost", estimated_cost)
            
            return {
                "total_runs": total_runs,
                "successful_runs": successful_runs,
                "failed_runs": failed_runs,
                "success_rate": (successful_runs / total_runs) * 100 if total_runs > 0 else 0,
                "average_latency_seconds": avg_latency,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": total_tokens,
                "estimated_cost_usd": estimated_cost
            }
            
        except Exception as e:
            logger.error(f"Failed to get LangSmith metrics: {e}")
            sentry_sdk.capture_exception(e)
            return {"error": str(e)}
    
    async def get_cost_projection(self) -> Dict:
        """Get cost projection for the next month based on current usage."""
        try:
            # Get current month's token usage
            llm_tokens = [v.value for v in self.metrics["llm_tokens_used"].values]
            if not llm_tokens:
                return {
                    "current_usage_tokens": 0,
                    "projected_monthly_tokens": 0,
                    "projected_monthly_cost_usd": 0
                }
            
            # Calculate daily average
            days_with_data = min(30, len(llm_tokens))
            daily_average = sum(llm_tokens) / days_with_data
            
            # Project for 30 days
            projected_monthly = daily_average * 30
            
            # Estimate cost (simplified model)
            # Assuming 75% input tokens, 25% output tokens with OpenAI GPT-4 pricing
            input_ratio = 0.75
            output_ratio = 0.25
            projected_input_tokens = projected_monthly * input_ratio
            projected_output_tokens = projected_monthly * output_ratio
            
            projected_cost = (projected_input_tokens * 0.0000005) + (projected_output_tokens * 0.0000015)
            
            return {
                "current_usage_tokens": sum(llm_tokens),
                "projected_monthly_tokens": projected_monthly,
                "projected_monthly_cost_usd": projected_cost
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate cost projection: {e}")
            sentry_sdk.capture_exception(e)
            return {"error": str(e)}
    
    async def get_system_health(self) -> Dict:
        """Get overall system health status."""
        # Check for recent critical alerts
        recent_critical = [
            a for a in self.alerts 
            if a.level == "CRITICAL" 
            and not a.resolved 
            and (datetime.now() - a.timestamp) < timedelta(hours=24)
        ]
        
        # Get error rate
        recent_errors = 0
        recent_requests = 0
        
        if "error_count" in self.metrics and "api_requests" in self.metrics:
            recent_errors = sum(
                v.value for v in self.metrics["error_count"].values
                if (datetime.now() - v.timestamp) < timedelta(hours=24)
            )
            recent_requests = sum(
                v.value for v in self.metrics["api_requests"].values
                if (datetime.now() - v.timestamp) < timedelta(hours=24)
            )
        
        error_rate = (recent_errors / recent_requests) * 100 if recent_requests > 0 else 0
        
        # Determine overall health
        if len(recent_critical) > 0:
            status = "critical"
        elif error_rate > 5:
            status = "degraded"
        else:
            status = "healthy"
        
        return {
            "status": status,
            "unresolved_critical_alerts": len(recent_critical),
            "error_rate_24h": error_rate,
            "api_requests_24h": recent_requests,
            "last_updated": datetime.now().isoformat()
        }


# Create a global instance
monitoring_service = None

def get_monitoring_service(
    supabase_client: Optional[SupabaseService] = None,
    langsmith_client: Optional[LangSmithService] = None
) -> MonitoringService:
    """Get or create the monitoring service singleton."""
    global monitoring_service
    if monitoring_service is None:
        monitoring_service = MonitoringService(
            supabase_client=supabase_client,
            langsmith_client=langsmith_client
        )
    return monitoring_service