"""
Test fixtures for the Interview Evaluator application.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient

@pytest.fixture
def mock_supabase():
    """Mock the Supabase client."""
    mock = MagicMock()
    mock.is_connected.return_value = True
    
    # Create a method that returns a chainable mock for table queries
    table_mock = MagicMock()
    select_mock = MagicMock()
    insert_mock = MagicMock()
    update_mock = MagicMock()
    delete_mock = MagicMock()
    execute_mock = AsyncMock()
    
    # Set up the chain mocks
    table_mock.select.return_value = select_mock
    table_mock.insert.return_value = insert_mock
    table_mock.update.return_value = update_mock
    table_mock.delete.return_value = delete_mock
    
    select_mock.eq.return_value = select_mock
    select_mock.neq.return_value = select_mock
    select_mock.limit.return_value = select_mock
    select_mock.order.return_value = select_mock
    select_mock.range.return_value = select_mock
    select_mock.execute.return_value = execute_mock
    
    insert_mock.execute.return_value = execute_mock
    update_mock.eq.return_value = update_mock
    update_mock.execute.return_value = execute_mock
    delete_mock.eq.return_value = delete_mock
    delete_mock.execute.return_value = execute_mock
    
    # Configure execute to return data
    execute_mock.data = [
        {
            "id": "test-interview-id",
            "user_id": "test-user-id",
            "candidate_name": "Test Candidate",
            "status": "evaluated",
            "created_at": "2023-01-01T00:00:00.000Z",
            "updated_at": "2023-01-01T00:00:00.000Z"
        }
    ]
    
    # Set up the table method in the main mock
    mock.table.return_value = table_mock
    
    return mock


@pytest.fixture
def mock_langsmith():
    """Mock the LangSmith client."""
    mock = MagicMock()
    
    # Configure trace_run to return a trace ID
    mock.trace_run = AsyncMock(return_value="test-trace-id")
    
    # Configure list_runs to return some sample runs
    mock.list_runs = AsyncMock(return_value=[
        {
            "id": "test-run-id",
            "name": "test-run",
            "start_time": "2023-01-01T00:00:00.000Z",
            "end_time": "2023-01-01T00:00:01.000Z",
            "input_tokens": 100,
            "output_tokens": 50,
            "error": None,
            "extra": {
                "model_name": "gpt-4"
            }
        }
    ])
    
    return mock


@pytest.fixture
def mock_auth():
    """Mock the authentication middleware."""
    return MagicMock()


@pytest.fixture
def test_client(mock_supabase, mock_langsmith, mock_auth):
    """Create a test client for the FastAPI app with mocked dependencies."""
    from app.main import app
    
    # Create a test client
    client = TestClient(app)
    
    # Override authentication middleware for testing
    client.app.dependency_overrides = {
        # We would normally override the auth dependency here
    }
    
    return client