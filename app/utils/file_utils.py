import os
import logging
import tempfile
from fastapi import UploadFile
from typing import Optional, Tuple
import uuid

logger = logging.getLogger(__name__)

ALLOWED_EXTENSIONS = [".txt"]  # Limit to .txt files for MVP
MAX_FILE_SIZE_MB = 5  # Maximum file size in MB

async def save_uploaded_file(file: UploadFile) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Save an uploaded file to a temporary location
    
    Returns:
        Tuple containing:
        - Success status (bool)
        - File path if saved successfully, None otherwise
        - Error message if failed, None otherwise
    """
    try:
        # Check file extension
        _, file_extension = os.path.splitext(file.filename)
        if file_extension.lower() not in ALLOWED_EXTENSIONS:
            return False, None, f"File type not allowed. Please upload a file with one of these extensions: {', '.join(ALLOWED_EXTENSIONS)}"
        
        # Create a unique filename
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        temp_dir = tempfile.gettempdir()
        file_path = os.path.join(temp_dir, unique_filename)
        
        # Read file content and check size
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)  # Convert bytes to MB
        
        if file_size_mb > MAX_FILE_SIZE_MB:
            return False, None, f"File size exceeds maximum allowed size of {MAX_FILE_SIZE_MB}MB"
        
        # Write file to disk
        with open(file_path, "wb") as f:
            f.write(content)
            
        logger.info(f"File saved successfully: {file_path}")
        return True, file_path, None
        
    except Exception as e:
        logger.error(f"Error saving file: {e}", exc_info=True)
        return False, None, f"Error saving file: {str(e)}"


async def read_file_content(file_path: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Read the content of a file
    
    Returns:
        Tuple containing:
        - Success status (bool)
        - File content if read successfully, None otherwise
        - Error message if failed, None otherwise
    """
    try:
        if not os.path.exists(file_path):
            return False, None, f"File not found: {file_path}"
            
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
            
        return True, content, None
        
    except Exception as e:
        logger.error(f"Error reading file: {e}", exc_info=True)
        return False, None, f"Error reading file: {str(e)}"