import time
import requests
import config as cfg
from logging_Setup import get_logger
import os

ALLWOED_EXTS = cfg.ALLWOED_EXTENSIONS

logger=get_logger(__name__)

class FileManagerError(Exception):
    """Base exception for FileManager errors"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code or "FM-000"
        self.details = details or {}
        self.timestamp = time.time()
        
        # Use WARNING level by default for all errors except DownloadError
        logger.warning(f"[{self.error_code}] {message} | Details: {self.details}")
        
        super().__init__(self.message)
    
    def __str__(self):
        # Return only the message without the error code for API responses
        return f"{self.message}"
    
    def to_dict(self):
        """Convert exception to a dictionary for API responses"""
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp
        }

class FileSizeError(FileManagerError):
    """Raised when file size exceeds limit"""
    def __init__(self, message, file_size=None, size_limit=None):
        details = {
            "file_size": file_size,
            "size_limit": size_limit,
            "size_exceeded_by": file_size - size_limit if file_size and size_limit else None
        }
        super().__init__(message, "FM-001", details)

class FileTypeError(FileManagerError):
    """Raised when file type is not allowed"""
    def __init__(self, message, file_ext=None, allowed_exts=None):
        details = {
            "file_extension": file_ext,
            "allowed_extensions": allowed_exts or ALLWOED_EXTS
        }
        super().__init__(message, "FM-002", details)

class DownloadError(FileManagerError):
    """Raised when download fails"""
    def __init__(self, message, url=None, status_code=None, original_error=None):
        details = {
            "url": url,
            "status_code": status_code,
            "original_error": str(original_error) if original_error else None
        }
        
        # Set instance variables first so they're available for logging
        self.message = message
        self.error_code = "FM-003"
        self.details = details
        self.timestamp = time.time()
        
        # Override the parent class logging to use ERROR level instead of WARNING
        logger.error(f"[{self.error_code}] {message} | Details: {self.details}")
        
        super(Exception, self).__init__(self.message)
        
        # Additional logic - check if it's a network issue
        if original_error and isinstance(original_error, requests.exceptions.ConnectionError):
            logger.warning(f"Network connectivity issue detected when downloading {url}")
            self.details["error_type"] = "network_connectivity"
        elif status_code and status_code >= 400:
            logger.error(f"HTTP error {status_code} when downloading {url}")
            self.details["error_type"] = "http_error"

class FileAlreadyExistsError(FileManagerError):
    """Raised when a file already exists in the system"""
    def __init__(self, message, file_path=None, file_name=None):
        details = {
            "file_path": file_path,
            "file_name": file_name or (os.path.basename(file_path) if file_path else None)
        }
        super().__init__(message, "FM-004", details)