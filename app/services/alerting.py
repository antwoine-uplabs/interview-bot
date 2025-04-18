"""
Alerting service for the interview evaluator application.
Handles alert creation, notification, and management.
"""

import logging
import os
from datetime import datetime
from typing import Dict, List, Optional, Union

import httpx
import sentry_sdk
from fastapi import HTTPException
from pydantic import BaseModel, Field

from app.services.monitoring import get_monitoring_service

# Configure logger
logger = logging.getLogger(__name__)

# Constants
WEBHOOK_URLS = {
    "slack": os.getenv("SLACK_WEBHOOK_URL"),
    "teams": os.getenv("TEAMS_WEBHOOK_URL"),
    "custom": os.getenv("CUSTOM_WEBHOOK_URL"),
}

ALERT_SEVERITY = {
    "INFO": 0,
    "WARNING": 1,
    "ERROR": 2,
    "CRITICAL": 3
}

# Alert thresholds
THRESHOLDS = {
    "error_rate": 5.0,  # Error rate percentage
    "api_latency": 1000,  # API latency in ms
    "evaluation_time": 60.0,  # Evaluation time in seconds
    "token_usage_daily": 100000,  # Token usage per day
    "cost_daily": 10.0,  # Cost per day in USD
}


class AlertRule(BaseModel):
    """Alert rule configuration."""
    id: str
    name: str
    description: str
    metric: str
    threshold: float
    comparison: str = Field(..., description="gt, lt, eq, gte, lte")
    severity: str
    enabled: bool = True


class Alert(BaseModel):
    """Alert model."""
    id: str
    timestamp: datetime
    rule_id: str
    severity: str
    message: str
    metric: str
    value: float
    threshold: float
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_at: Optional[datetime] = None
    notified: bool = False


class AlertingService:
    """Service for managing alerts and notifications."""

    def __init__(self):
        """Initialize the alerting service."""
        self.alerts: List[Alert] = []
        self.rules: List[AlertRule] = [
            AlertRule(
                id="error-rate",
                name="High Error Rate",
                description="Error rate exceeds threshold",
                metric="error_rate",
                threshold=THRESHOLDS["error_rate"],
                comparison="gt",
                severity="WARNING",
            ),
            AlertRule(
                id="api-latency",
                name="High API Latency",
                description="API latency exceeds threshold",
                metric="api_latency",
                threshold=THRESHOLDS["api_latency"],
                comparison="gt",
                severity="WARNING",
            ),
            AlertRule(
                id="evaluation-time",
                name="Long Evaluation Time",
                description="Interview evaluation time exceeds threshold",
                metric="evaluation_time",
                threshold=THRESHOLDS["evaluation_time"],
                comparison="gt",
                severity="WARNING",
            ),
            AlertRule(
                id="token-usage",
                name="High Token Usage",
                description="Daily token usage exceeds threshold",
                metric="token_usage_daily",
                threshold=THRESHOLDS["token_usage_daily"],
                comparison="gt",
                severity="ERROR",
            ),
            AlertRule(
                id="cost-threshold",
                name="High Cost",
                description="Daily cost exceeds threshold",
                metric="cost_daily",
                threshold=THRESHOLDS["cost_daily"],
                comparison="gt",
                severity="ERROR",
            ),
        ]
        
    async def check_alert_conditions(self) -> List[Alert]:
        """Check all alert conditions and create alerts as needed."""
        monitoring = get_monitoring_service()
        new_alerts = []
        
        # Get metrics from monitoring service
        metrics = await monitoring.get_metrics()
        langsmith_metrics = await monitoring.get_langsmith_metrics()
        cost_projection = await monitoring.get_cost_projection()
        system_health = await monitoring.get_system_health()
        
        # Calculate derived metrics
        error_rate = system_health.get("error_rate_24h", 0)
        daily_cost = cost_projection.get("projected_monthly_cost_usd", 0) / 30
        daily_tokens = cost_projection.get("projected_monthly_tokens", 0) / 30
        
        # Extend metrics with calculated values
        metrics_values = {
            "error_rate": error_rate,
            "cost_daily": daily_cost,
            "token_usage_daily": daily_tokens,
        }
        
        # Check each alert rule
        for rule in self.rules:
            if not rule.enabled:
                continue
                
            # Get the metric value
            value = metrics_values.get(rule.metric)
            
            # Skip if metric not available
            if value is None:
                continue
                
            # Check threshold
            alert_triggered = False
            
            if rule.comparison == "gt" and value > rule.threshold:
                alert_triggered = True
            elif rule.comparison == "lt" and value < rule.threshold:
                alert_triggered = True
            elif rule.comparison == "eq" and value == rule.threshold:
                alert_triggered = True
            elif rule.comparison == "gte" and value >= rule.threshold:
                alert_triggered = True
            elif rule.comparison == "lte" and value <= rule.threshold:
                alert_triggered = True
                
            if alert_triggered:
                # Create alert
                alert_id = f"{rule.id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
                
                # Format the message
                message = f"{rule.name}: {rule.metric} is {value} (threshold: {rule.threshold})"
                
                # Create the alert
                alert = Alert(
                    id=alert_id,
                    timestamp=datetime.now(),
                    rule_id=rule.id,
                    severity=rule.severity,
                    message=message,
                    metric=rule.metric,
                    value=value,
                    threshold=rule.threshold,
                )
                
                # Add to alerts list
                self.alerts.append(alert)
                new_alerts.append(alert)
                
                # Log the alert
                log_level = rule.severity.lower()
                log_method = getattr(logger, log_level, logger.info)
                log_method(f"Alert triggered: {message}")
                
                # Create alert in monitoring service
                monitoring_service = get_monitoring_service()
                await monitoring_service.create_alert(
                    level=rule.severity,
                    message=message,
                    source="alerting_service"
                )
                
                # Send notification for critical and error alerts
                if rule.severity in ["CRITICAL", "ERROR"]:
                    await self.send_notification(alert)
                    alert.notified = True
        
        return new_alerts
    
    async def get_alerts(self, 
                         severity: Optional[str] = None,
                         resolved: Optional[bool] = None) -> List[Alert]:
        """Get alerts filtered by severity and resolved status."""
        filtered_alerts = self.alerts
        
        if severity:
            filtered_alerts = [a for a in filtered_alerts if a.severity == severity]
            
        if resolved is not None:
            filtered_alerts = [a for a in filtered_alerts if a.resolved == resolved]
            
        # Sort by timestamp (newest first)
        filtered_alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        return filtered_alerts
    
    async def get_alert(self, alert_id: str) -> Optional[Alert]:
        """Get an alert by ID."""
        for alert in self.alerts:
            if alert.id == alert_id:
                return alert
                
        return None
    
    async def resolve_alert(self, alert_id: str) -> Alert:
        """Resolve an alert."""
        alert = await self.get_alert(alert_id)
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert with ID '{alert_id}' not found")
            
        alert.resolved = True
        alert.resolved_at = datetime.now()
        
        # Log the resolution
        logger.info(f"Alert {alert_id} resolved: {alert.message}")
        
        return alert
    
    async def acknowledge_alert(self, alert_id: str) -> Alert:
        """Acknowledge an alert."""
        alert = await self.get_alert(alert_id)
        
        if not alert:
            raise HTTPException(status_code=404, detail=f"Alert with ID '{alert_id}' not found")
            
        alert.acknowledged = True
        alert.acknowledged_at = datetime.now()
        
        # Log the acknowledgement
        logger.info(f"Alert {alert_id} acknowledged: {alert.message}")
        
        return alert
    
    async def send_notification(self, alert: Alert) -> bool:
        """Send notification for an alert."""
        # If no webhooks are configured, log and return
        if not any(WEBHOOK_URLS.values()):
            logger.warning("No webhook URLs configured for alerting")
            return False
            
        # Prepare notification content
        notification = {
            "title": f"[{alert.severity}] {alert.metric.upper()} ALERT",
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
            "metric": alert.metric,
            "value": alert.value,
            "threshold": alert.threshold,
            "id": alert.id
        }
        
        success = False
        
        # Send to Slack
        if WEBHOOK_URLS["slack"]:
            try:
                slack_payload = {
                    "text": f"🚨 *{notification['title']}*",
                    "attachments": [
                        {
                            "color": "#FF0000" if alert.severity == "CRITICAL" else "#FFA500",
                            "fields": [
                                {"title": "Message", "value": notification["message"], "short": False},
                                {"title": "Metric", "value": notification["metric"], "short": True},
                                {"title": "Value", "value": str(notification["value"]), "short": True},
                                {"title": "Threshold", "value": str(notification["threshold"]), "short": True},
                                {"title": "Time", "value": notification["timestamp"], "short": True},
                                {"title": "ID", "value": notification["id"], "short": True}
                            ],
                            "footer": "Interview Evaluator Alerts"
                        }
                    ]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        WEBHOOK_URLS["slack"],
                        json=slack_payload,
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Slack notification sent for alert {alert.id}")
                        success = True
                    else:
                        logger.error(f"Failed to send Slack notification: {response.text}")
                        
            except Exception as e:
                logger.error(f"Error sending Slack notification: {e}")
                sentry_sdk.capture_exception(e)
        
        # Send to Teams
        if WEBHOOK_URLS["teams"]:
            try:
                teams_payload = {
                    "@type": "MessageCard",
                    "@context": "http://schema.org/extensions",
                    "themeColor": "FF0000" if alert.severity == "CRITICAL" else "FFA500",
                    "summary": notification["title"],
                    "sections": [
                        {
                            "activityTitle": f"🚨 {notification['title']}",
                            "facts": [
                                {"name": "Message", "value": notification["message"]},
                                {"name": "Metric", "value": notification["metric"]},
                                {"name": "Value", "value": str(notification["value"])},
                                {"name": "Threshold", "value": str(notification["threshold"])},
                                {"name": "Time", "value": notification["timestamp"]},
                                {"name": "ID", "value": notification["id"]}
                            ],
                            "markdown": True
                        }
                    ]
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        WEBHOOK_URLS["teams"],
                        json=teams_payload,
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Teams notification sent for alert {alert.id}")
                        success = True
                    else:
                        logger.error(f"Failed to send Teams notification: {response.text}")
                        
            except Exception as e:
                logger.error(f"Error sending Teams notification: {e}")
                sentry_sdk.capture_exception(e)
        
        # Send to custom webhook
        if WEBHOOK_URLS["custom"]:
            try:
                custom_payload = {
                    "alert": {
                        "id": alert.id,
                        "severity": alert.severity,
                        "message": alert.message,
                        "timestamp": alert.timestamp.isoformat(),
                        "metric": alert.metric,
                        "value": alert.value,
                        "threshold": alert.threshold
                    }
                }
                
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        WEBHOOK_URLS["custom"],
                        json=custom_payload,
                        timeout=10.0
                    )
                    
                    if response.status_code == 200:
                        logger.info(f"Custom webhook notification sent for alert {alert.id}")
                        success = True
                    else:
                        logger.error(f"Failed to send custom webhook notification: {response.text}")
                        
            except Exception as e:
                logger.error(f"Error sending custom webhook notification: {e}")
                sentry_sdk.capture_exception(e)
        
        return success
    
    async def get_alert_rules(self) -> List[AlertRule]:
        """Get all alert rules."""
        return self.rules
    
    async def update_alert_rule(self, rule_id: str, updates: Dict) -> AlertRule:
        """Update an alert rule."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                # Update the rule
                for key, value in updates.items():
                    if hasattr(rule, key):
                        setattr(rule, key, value)
                        
                # Log the update
                logger.info(f"Alert rule {rule_id} updated: {updates}")
                
                return rule
                
        raise HTTPException(status_code=404, detail=f"Alert rule with ID '{rule_id}' not found")
    
    async def add_alert_rule(self, rule: AlertRule) -> AlertRule:
        """Add a new alert rule."""
        # Check for duplicate ID
        for existing_rule in self.rules:
            if existing_rule.id == rule.id:
                raise HTTPException(status_code=400, detail=f"Alert rule with ID '{rule.id}' already exists")
                
        # Add the rule
        self.rules.append(rule)
        
        # Log the addition
        logger.info(f"New alert rule added: {rule.id} - {rule.name}")
        
        return rule
    
    async def delete_alert_rule(self, rule_id: str) -> bool:
        """Delete an alert rule."""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                # Remove the rule
                self.rules.pop(i)
                
                # Log the deletion
                logger.info(f"Alert rule {rule_id} deleted")
                
                return True
                
        raise HTTPException(status_code=404, detail=f"Alert rule with ID '{rule_id}' not found")


# Create a global instance
alerting_service = None

def get_alerting_service() -> AlertingService:
    """Get or create the alerting service singleton."""
    global alerting_service
    if alerting_service is None:
        alerting_service = AlertingService()
    return alerting_service