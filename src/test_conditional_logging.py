#!/usr/bin/env python3
"""
Test script to demonstrate conditional logging behavior.
This will show different behavior for local vs Azure Function environments.
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
    get_session_log_file,
    is_azure_function_environment,
    reset_session_log
)

def test_local_environment():
    """Test logging in local environment."""
    print("=== Testing Local Environment ===")
    print(f"Is Azure Function Environment: {is_azure_function_environment()}")
    
    # Set up logging
    log_file = setup_timestamped_logging(logging.INFO)
    if log_file:
        print(f"✓ Local logging initialized: {log_file}")
    else:
        print("✗ No local log file created")
    
    # Test function-specific logging
    logger, func_log_file = setup_function_specific_logging('TestFunction', logging.INFO)
    logger.info("This is a test message from local environment")
    
    if func_log_file:
        print(f"✓ Function logging initialized: {func_log_file}")
    else:
        print("✗ No function log file created")
    
    return log_file

def test_simulated_azure_environment():
    """Test logging by simulating Azure Function environment."""
    print("\n=== Testing Simulated Azure Function Environment ===")
    
    # Reset session first
    reset_session_log()
    
    # Simulate Azure Function environment
    os.environ['AZURE_FUNCTIONS_ENVIRONMENT'] = 'Development'
    
    print(f"Is Azure Function Environment: {is_azure_function_environment()}")
    
    # Set up logging
    log_file = setup_timestamped_logging(logging.INFO)
    if log_file:
        print(f"✗ Local log file created when it shouldn't be: {log_file}")
    else:
        print("✓ No local log file created (using Azure logging)")
    
    # Test function-specific logging
    logger, func_log_file = setup_function_specific_logging('TestAzureFunction', logging.INFO)
    logger.info("This is a test message from simulated Azure environment")
    
    if func_log_file:
        print(f"✗ Function log file created when it shouldn't be: {func_log_file}")
    else:
        print("✓ No function log file created (using Azure logging)")
    
    # Clean up environment variable
    del os.environ['AZURE_FUNCTIONS_ENVIRONMENT']
    
    return log_file

def show_environment_detection():
    """Show how environment detection works."""
    print("\n=== Environment Detection ===")
    
    azure_env_vars = [
        'AZURE_FUNCTIONS_ENVIRONMENT',
        'WEBSITE_SITE_NAME', 
        'FUNCTIONS_WORKER_RUNTIME'
    ]
    
    print("Azure Function environment variables:")
    for var in azure_env_vars:
        value = os.getenv(var)
        print(f"  {var}: {value if value else 'Not set'}")
    
    print(f"\nDetected as Azure Function: {is_azure_function_environment()}")

if __name__ == "__main__":
    print("Testing conditional logging system...")
    print("=" * 60)
    
    # Show environment detection
    show_environment_detection()
    
    # Test 1: Local environment
    local_log = test_local_environment()
    
    # Test 2: Simulated Azure environment
    azure_log = test_simulated_azure_environment()
    
    print("\n" + "=" * 60)
    print("Conditional logging tests completed!")
    print(f"Local environment created log file: {local_log is not None}")
    print(f"Azure environment created log file: {azure_log is not None}")
    print("\nThis demonstrates that custom logging is only used for local MCP development.")
