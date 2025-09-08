"""Utility functions for the Storefront Agent."""

import json
import asyncio
from typing import Any, Dict, List, Optional, Union
from loguru import logger


def format_json_response(data: Any, indent: int = 2) -> str:
    """
    Format data as pretty-printed JSON.
    
    Args:
        data: Data to format
        indent: JSON indentation level
        
    Returns:
        Formatted JSON string
    """
    try:
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except (TypeError, ValueError) as e:
        logger.error(f"Error formatting JSON: {str(e)}")
        return str(data)


def safe_json_parse(json_string: str, default: Any = None) -> Any:
    """
    Safely parse JSON string with fallback.
    
    Args:
        json_string: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_string)
    except (json.JSONDecodeError, TypeError) as e:
        logger.warning(f"Failed to parse JSON: {str(e)}")
        return default


def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """
    Validate that required fields are present in data.
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
        
    Returns:
        List of missing fields
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    return missing_fields


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to maximum length.
    
    Args:
        text: String to truncate
        max_length: Maximum length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def sanitize_input(text: str) -> str:
    """
    Sanitize user input for safety.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00']
    sanitized = text
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Limit length
    sanitized = sanitized[:1000]
    
    return sanitized.strip()


async def retry_async(
    func,
    max_retries: int = 3,
    delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple = (Exception,)
) -> Any:
    """
    Retry an async function with exponential backoff.
    
    Args:
        func: Async function to retry
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff_factor: Factor to multiply delay by after each retry
        exceptions: Tuple of exceptions to catch and retry on
        
    Returns:
        Result of the function
        
    Raises:
        Last exception if all retries fail
    """
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            return await func()
        except exceptions as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = delay * (backoff_factor ** attempt)
                logger.warning(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {wait_time:.2f}s...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries + 1} attempts failed. Last error: {str(e)}")
    
    raise last_exception


def create_error_response(error_message: str, error_code: str = "UNKNOWN_ERROR") -> Dict[str, Any]:
    """
    Create a standardized error response.
    
    Args:
        error_message: Error message
        error_code: Error code
        
    Returns:
        Standardized error response dictionary
    """
    return {
        "success": False,
        "error": {
            "message": error_message,
            "code": error_code
        },
        "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else None
    }


def create_success_response(data: Any, message: str = "Operation completed successfully") -> Dict[str, Any]:
    """
    Create a standardized success response.
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        Standardized success response dictionary
    """
    return {
        "success": True,
        "message": message,
        "data": data,
        "timestamp": asyncio.get_event_loop().time() if asyncio.get_event_loop().is_running() else None
    }


class StorefrontAgentException(Exception):
    """Base exception for Storefront Agent."""
    
    def __init__(self, message: str, error_code: str = "UNKNOWN_ERROR", details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}


class ConfigurationError(StorefrontAgentException):
    """Exception for configuration-related errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "CONFIGURATION_ERROR", details)


class MCPConnectionError(StorefrontAgentException):
    """Exception for MCP connection errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "MCP_CONNECTION_ERROR", details)


class LLMProcessingError(StorefrontAgentException):
    """Exception for LLM processing errors."""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "LLM_PROCESSING_ERROR", details)


def setup_error_handling():
    """Setup global error handling for the application."""
    import sys
    
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Global exception handler."""
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        logger.error(
            "Uncaught exception",
            exc_info=(exc_type, exc_value, exc_traceback)
        )
    
    sys.excepthook = handle_exception
