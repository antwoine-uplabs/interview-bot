import pytest
from unittest.mock import MagicMock, patch
from app.services.supabase_client import SupabaseService

@pytest.fixture
def mock_supabase_client():
    with patch('app.services.supabase_client.create_client') as mock_create:
        mock_client = MagicMock()
        mock_create.return_value = mock_client
        
        # Configure supabase table operations
        mock_table = MagicMock()
        mock_client.table.return_value = mock_table
        
        # Configure auth operations
        mock_auth = MagicMock()
        mock_client.auth = mock_auth
        
        yield {
            'client': mock_client,
            'table': mock_table,
            'auth': mock_auth
        }

def test_is_connected(mock_supabase_client):
    """Test checking if Supabase client is connected"""
    service = SupabaseService()
    service.client = mock_supabase_client['client']
    
    assert service.is_connected() is True
    
    service.client = None
    assert service.is_connected() is False

def test_get_total_interviews(mock_supabase_client):
    """Test retrieving total interviews count"""
    # Setup mock return values
    mock_query = MagicMock()
    mock_supabase_client['table'].select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    
    # Setup result with count property
    mock_result = MagicMock()
    mock_result.count = 5
    mock_query.execute.return_value = mock_result
    
    # Create service with mocked client
    service = SupabaseService()
    service.client = mock_supabase_client['client']
    
    # Test with user_id
    result = service.get_total_interviews(user_id="test-user")
    assert result == 5
    mock_supabase_client['table'].select.assert_called_with('count', count='exact')
    
    # Test without user_id
    result = service.get_total_interviews()
    assert result == 5

def test_get_usage_statistics(mock_supabase_client):
    """Test retrieving usage statistics"""
    # Setup mock return values for interview query
    mock_query = MagicMock()
    mock_supabase_client['table'].select.return_value = mock_query
    mock_query.eq.return_value = mock_query
    mock_query.gte.return_value = mock_query
    
    # Setup sample interview data
    mock_query.execute.return_value.data = [
        {
            'id': 'id1',
            'status': 'evaluated',
            'created_at': '2023-01-01T00:00:00Z'
        },
        {
            'id': 'id2',
            'status': 'processing',
            'created_at': '2023-01-01T00:00:00Z'
        }
    ]
    
    # Create service with mocked client
    service = SupabaseService()
    service.client = mock_supabase_client['client']
    
    # Test fetching usage statistics
    result = service.get_usage_statistics(user_id="test-user", days=7)
    
    assert result["total_interviews"] == 2
    assert "by_status" in result
    assert "daily_counts" in result
    assert result["by_status"]["evaluated"] == 1
    assert result["by_status"]["processing"] == 1