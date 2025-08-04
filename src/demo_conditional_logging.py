#!/usr/bin/env python3
"""
Example demonstrating the conditional logging in a simulated Azure Function context.
This shows how the same code behaves differently in local vs Azure environments.
"""

import os
import sys
import logging

# Add the src directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Simulate the imports and setup from function_app.py
from utils.log_config import setup_timestamped_logging, cleanup_old_logs, is_azure_function_environment

def simulate_function_app_startup():
    """Simulate the function app startup process."""
    print("=== Simulating Azure Function App Startup ===")
    
    # This is exactly what happens in function_app.py
    log_file_path = setup_timestamped_logging(logging.INFO)
    if log_file_path:
        logging.info(f"Local MCP development logging to: {log_file_path}")
        cleanup_old_logs(days_to_keep=7)
        print(f"✓ Local development mode: Logging to {log_file_path}")
    else:
        logging.info("Azure Function App started - using Azure's built-in logging")
        print("✓ Azure Functions mode: Using built-in Azure logging")

def test_local_vs_azure():
    """Test the same code in both environments."""
    
    # Test 1: Local environment (current)
    print("\n1. Testing in Local Environment:")
    print(f"   Environment detected as Azure Functions: {is_azure_function_environment()}")
    simulate_function_app_startup()
    
    # Test 2: Simulated Azure environment
    print("\n2. Testing in Simulated Azure Environment:")
    
    # Set Azure environment variable
    os.environ['FUNCTIONS_WORKER_RUNTIME'] = 'python'
    print(f"   Environment detected as Azure Functions: {is_azure_function_environment()}")
    simulate_function_app_startup()
    
    # Clean up
    del os.environ['FUNCTIONS_WORKER_RUNTIME']

if __name__ == "__main__":
    print("Azure Function Conditional Logging Demo")
    print("=" * 50)
    
    print("This demonstrates how the same code behaves differently")
    print("depending on whether it's running locally or in Azure Functions.")
    
    test_local_vs_azure()
    
    print("\n" + "=" * 50)
    print("Summary:")
    print("- Local development: Creates timestamped log files")
    print("- Azure Functions: Uses Azure's built-in logging system")
    print("- No code changes needed - automatic environment detection!")
