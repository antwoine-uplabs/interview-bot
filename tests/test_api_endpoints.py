import pytest
from fastapi.testclient import TestClient

# Mock the necessary modules to avoid loading the main app directly
import sys
from unittest.mock import MagicMock, patch

# Create mocks for problematic imports
sys.modules['langsmith'] = MagicMock()
sys.modules['langchain'] = MagicMock()
sys.modules['langchain.callbacks'] = MagicMock()
sys.modules['langchain_community'] = MagicMock()
sys.modules['langchain_community.callbacks'] = MagicMock()
sys.modules['langchain_community.callbacks.langsmith'] = MagicMock()

# Now we can import the app
from app.main import app

client = TestClient(app)

def test_health_endpoint_success(mock_supabase, mock_langsmith):
    """Test health endpoint returns OK when all services are running"""
    mock_supabase.is_connected.return_value = True
    mock_langsmith.is_configured.return_value = True
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert "supabase" in response.json()["dependencies"]
    assert "langsmith" in response.json()["dependencies"]
    assert response.json()["dependencies"]["supabase"] == "connected"
    assert response.json()["dependencies"]["langsmith"] == "configured"

def test_health_endpoint_degraded(mock_supabase, mock_langsmith):
    """Test health endpoint returns degraded when services are down"""
    mock_supabase.is_connected.return_value = False
    mock_langsmith.is_configured.return_value = False
    
    response = client.get("/health")
    
    assert response.status_code == 200
    assert response.json()["status"] == "degraded"
    assert response.json()["dependencies"]["supabase"] == "disconnected"
    assert response.json()["dependencies"]["langsmith"] == "not_configured"

def test_status_endpoint(test_client, mock_supabase, mock_auth):
    """Test the interview status endpoint"""
    response = test_client.get("/status/test-interview-id")
    
    assert response.status_code == 200
    assert response.json()["interview_id"] == "test-interview-id"
    assert response.json()["status"] == "evaluated"
    assert response.json()["candidate_name"] == "Test Candidate"

def test_get_evaluation_results(test_client, mock_supabase, mock_auth):
    """Test fetching evaluation results"""
    response = test_client.get("/results/test-interview-id")
    
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["overall_score"] == 7.5
    assert response.json()["candidate_name"] == "Test Candidate"
    assert len(response.json()["criteria_evaluations"]) > 0
    assert "strengths" in response.json()
    assert "weaknesses" in response.json()