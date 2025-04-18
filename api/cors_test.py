# Add this file to your API directory
from fastapi import APIRouter

router = APIRouter()

@router.get("/cors-test")
async def test_cors():
    """
    Test endpoint to verify CORS configuration is working
    """
    return {
        "status": "success",
        "message": "CORS is properly configured",
        "cors_test": True
    }
