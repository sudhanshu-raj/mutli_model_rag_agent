import logging
import os
from datetime import datetime

# Default log directory - create if it doesn't exist
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
os.makedirs(LOG_DIR, exist_ok=True)

# Default log file with timestamp
DEFAULT_LOG_FILE = os.path.join(LOG_DIR, f"app_{datetime.now().strftime('%Y%m%d')}.log")

# Singleton to ensure we only configure the logging system once
_is_logging_configured = False

def configure_logging(log_file=None, log_level=logging.INFO):
    """
    Configure the logging system globally
    
    Args:
        log_file (str): Path to log file, defaults to logs/app_YYYYMMDD.log
        log_level (int): Logging level, defaults to INFO
    """
    global _is_logging_configured
    
    if _is_logging_configured:
        return
        
    log_file = log_file or DEFAULT_LOG_FILE
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Configure file handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    
    # Configure console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    _is_logging_configured = True
    
    # Log that the system is initialized
    root_logger.info(f"Logging system initialized. Log file: {log_file}")

def get_logger(name):
    """
    Get a logger with the specified name
    
    Args:
        name (str): Name for the logger
        
    Returns:
        Logger: Configured logger instance
    """
    # Ensure logging is configured
    if not _is_logging_configured:
        configure_logging()
        
    return logging.getLogger(name)