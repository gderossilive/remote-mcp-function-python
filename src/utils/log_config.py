"""
Shared Session Logging Configuration for Local MCP Development

This module provides logging utilities for local MCP development only.
When running in Azure Functions, the built-in Azure logging is used instead.

Key features for local development:
- Single shared log file per execution session
- Timestamped files with millisecond precision  
- All loggers (global and function-specific) write to the same file
- Automatic log file rotation between sessions
- Cleanup utilities for old log files
- Console and file output combined

Usage:
    # Initialize session logging (only for local development)
    log_file = setup_timestamped_logging()
    
    # Create function-specific loggers (will use same file locally)
    logger, _ = setup_function_specific_logging('MyFunction')
    
    # Reset for new session
    reset_session_log()
"""

import os
import logging
import datetime
from pathlib import Path

# Global variable to store the current log file path for the session
_current_log_file = None

def is_azure_function_environment():
    """
    Check if we're running in an Azure Function environment.
    Returns True if running in Azure Functions, False for local development.
    """
    # Azure Functions set specific environment variables
    return (
        os.getenv('AZURE_FUNCTIONS_ENVIRONMENT') is not None or
        os.getenv('WEBSITE_SITE_NAME') is not None or
        os.getenv('FUNCTIONS_WORKER_RUNTIME') is not None
    )

def get_or_create_session_log_file():
    """
    Get or create a single session log file that all loggers will use.
    This ensures all logging for a single execution goes to the same file.
    Only creates log files for local development.
    """
    global _current_log_file
    
    # Don't create log files in Azure Functions environment
    if is_azure_function_environment():
        return None
    
    if _current_log_file is None:
        # Create logs directory if it doesn't exist (in project root)
        logs_dir = Path(__file__).parent.parent.parent / "logs"
        logs_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for unique log file
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]  # Include milliseconds
        log_filename = f"mcp_session_{timestamp}.log"
        _current_log_file = logs_dir / log_filename
    
    return _current_log_file

def setup_timestamped_logging(log_level=logging.INFO):
    """
    Set up logging for local MCP development only.
    In Azure Functions, this returns None and uses default Azure logging.
    
    Args:
        log_level: The logging level (default: INFO)
    
    Returns:
        str: Log file path for local development, None for Azure Functions
    """
    # Skip custom logging in Azure Functions environment
    if is_azure_function_environment():
        return None
    
    # Get the shared session log file for local development
    log_filepath = get_or_create_session_log_file()
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filepath, mode='a'),  # Append mode for shared file
            logging.StreamHandler()  # Also log to console
        ],
        force=True  # Override any existing configuration
    )
    
    # Create a logger for this module
    logger = logging.getLogger(__name__)
    logger.info(f"Local MCP session logging initialized. Shared log file: {log_filepath}")
    
    return str(log_filepath)

def get_current_log_file():
    """
    Get the current session log file being used.
    """
    global _current_log_file
    if _current_log_file:
        return str(_current_log_file)
    return None

def get_session_log_file():
    """
    Get the current session log file path.
    If no session is active, returns None.
    """
    global _current_log_file
    return str(_current_log_file) if _current_log_file else None

def reset_session_log():
    """
    Reset the session log file. This will cause the next logging setup
    to create a new timestamped log file.
    """
    global _current_log_file
    _current_log_file = None

def setup_function_specific_logging(function_name, log_level=logging.INFO):
    """
    Set up logging for a specific function for local MCP development only.
    In Azure Functions, this returns a standard logger using Azure's logging.
    
    Args:
        function_name: Name of the function for the logger
        log_level: The logging level (default: INFO)
    
    Returns:
        tuple: (logger, log_file_path) where log_file_path is None for Azure Functions
    """
    # For Azure Functions, return a standard logger without custom file handling
    if is_azure_function_environment():
        logger = logging.getLogger(function_name)
        logger.setLevel(log_level)
        return logger, None
    
    # Get the shared session log file for local development
    log_filepath = get_or_create_session_log_file()
    
    # Create function-specific logger
    logger = logging.getLogger(function_name)
    logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplication
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add file handler (append mode for shared file)
    file_handler = logging.FileHandler(log_filepath, mode='a')
    file_handler.setLevel(log_level)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    logger.info(f"Local MCP function logging initialized for {function_name}. Shared log file: {log_filepath}")
    
    return logger, str(log_filepath)

def cleanup_old_logs(days_to_keep=7):
    """
    Clean up log files older than specified days.
    Only runs in local development environment.
    
    Args:
        days_to_keep: Number of days to keep logs (default: 7)
    """
    # Skip cleanup in Azure Functions environment
    if is_azure_function_environment():
        return
    
    logs_dir = Path(__file__).parent.parent.parent / "logs"
    if not logs_dir.exists():
        return
    
    cutoff_time = datetime.datetime.now() - datetime.timedelta(days=days_to_keep)
    deleted_count = 0
    
    for log_file in logs_dir.glob("*.log"):
        if log_file.stat().st_mtime < cutoff_time.timestamp():
            try:
                log_file.unlink()
                deleted_count += 1
            except OSError:
                pass  # File might be in use
    
    if deleted_count > 0:
        logger = logging.getLogger(__name__)
        logger.info(f"Cleaned up {deleted_count} old log files")
