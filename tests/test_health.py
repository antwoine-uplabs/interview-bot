"""
Tests for the health check endpoint.
"""

from fastapi.testclient import TestClient
import pytest
from unittest.mock import patch


def test_health_check(test_client):
    """Test that the health check endpoint returns 200 OK."""
    with patch('app.services.supabase_client.get_supabase_client'):
        with patch('app.services.langsmith.client.get_langsmith_client'):
            with patch('app.services.monitoring.get_monitoring_service') as mock_monitoring:
                # Configure the monitoring service mock
                mock_monitoring.return_value.get_system_health.return_value = {
                    "status": "healthy",
                    "unresolved_critical_alerts": 0,
                    "error_rate_24h": 0.0,
                    "api_requests_24h": 100,
                    "last_updated": "2023-01-01T00:00:00.000Z"
                }
                
                response = test_client.get("/health")
                
                assert response.status_code == 200
                assert response.json()["status"] == "healthy"
                assert response.json()["api_version"] == "1.0.0"
                assert "timestamp" in response.json()
                assert response.json()["supabase_status"] == "up"
                assert response.json()["langsmith_status"] == "up"