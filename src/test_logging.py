#!/usr/bin/env python3
"""
Test script to demonstrate shared session logging functionality.
Run this script to see all loggers writing to the same timestamped log file.
"""

import os
import sys
import time
import logging

# Add the src directory to the path so we can import our utilities
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.log_config import (
    setup_timestamped_logging, 
    setup_function_specific_logging, 
    get_current_log_file,
    get_session_log_file,
    reset_session_log
)

def test_shared_logging():
    """Test that all loggers write to the same shared log file."""
    print("=== Testing Shared Session Logging ===")
    
    # Set up global logging first
    log_file = setup_timestamped_logging(logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("=== Starting Shared Logging Test ===")
    logger.info("Global logger initialized")
    
    print(f"Session log file: {log_file}")
    
    # Create multiple function-specific loggers
    functions = ['GetServerMetadata', 'GetSqlMetadata', 'GetPatchingLevel']
    loggers = []
    
    for func_name in functions:
        func_logger, func_log_file = setup_function_specific_logging(func_name, logging.INFO)
        loggers.append((func_name, func_logger))
        
        # Verify they're all using the same log file
        print(f"{func_name} using log file: {func_log_file}")
        
        # Log some messages
        func_logger.info(f"Starting {func_name} execution")
        func_logger.info(f"Processing data for {func_name}")
        func_logger.warning(f"Warning from {func_name}")
        func_logger.info(f"Completed {func_name} execution")
    
    # Log some final messages with the global logger
    logger.info("All function loggers have been tested")
    logger.info("=== Shared Logging Test Complete ===")
    
    return log_file

def test_multiple_sessions():
    """Test that different execution sessions create different log files."""
    print("\n=== Testing Multiple Sessions ===")
    
    # First session
    session1_log = setup_timestamped_logging(logging.INFO)
    logger1 = logging.getLogger("session1")
    logger1.info("This is from session 1")
    print(f"Session 1 log file: {session1_log}")
    
    # Reset and create second session
    reset_session_log()
    time.sleep(0.1)  # Ensure different timestamp
    
    session2_log = setup_timestamped_logging(logging.INFO)
    logger2 = logging.getLogger("session2")
    logger2.info("This is from session 2")
    print(f"Session 2 log file: {session2_log}")
    
    # Verify they're different files
    if session1_log != session2_log:
        print("✓ Different sessions create different log files")
        return [session1_log, session2_log]
    else:
        print("✗ Sessions should create different log files")
        return [session1_log]

if __name__ == "__main__":
    print("Testing shared session logging system...")
    print("=" * 60)
    
    # Test 1: Shared logging within a session
    shared_log = test_shared_logging()
    
    # Test 2: Multiple sessions
    session_logs = test_multiple_sessions()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print(f"Total unique log files created: {len(set([shared_log] + session_logs))}")
    print("\nCheck the project root 'logs' directory for the timestamped log files.")
    print("Each session should have all its logs in a single shared file.")
