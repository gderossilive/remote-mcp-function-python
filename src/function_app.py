import json
import logging
import os

import azure.functions as func
from mcp_tools import (
    GetServerMetadata, GetSqlBpAssessment, GetSqlMetadata, GetPatchingLevel, GetAnomalies,
    GetSwChangesList, GetSwConfig, GetWinBpAssessment
)
from utils.log_config import setup_timestamped_logging, cleanup_old_logs, is_azure_function_environment

# Initialize logging - custom logging only for local development
log_file_path = setup_timestamped_logging(logging.INFO)
if log_file_path:
    logging.info(f"Local MCP development logging to: {log_file_path}")
    # Clean up old log files (keep last 7 days) - only for local development
    cleanup_old_logs(days_to_keep=7)
else:
    logging.info("Azure Function App started - using Azure's built-in logging")

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str, items_type: str = None):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description
        self.itemsType = items_type

    def to_dict(self):
        result = {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }
        
        # For array types, we need to specify the items property
        if self.propertyType == "array" and self.itemsType:
            result["items"] = {
                "type": self.itemsType
            }
        
        return result


# Tool properties for agent functions
tool_properties_subscription_id = [
    ToolProperty("subscription_id", "string", "Azure subscription ID to query Azure Resource Manager against"),
]

tool_properties_log_analytics = [
    ToolProperty("workspace_id", "string", "The workspace ID for the Log Analytics query."),
    ToolProperty("timespan", "string", "The timespan for the query (e.g., '30d' for 30 days)"),
]

tool_properties_log_analytics_with_server = [
    ToolProperty("workspace_id", "string", "The workspace ID for the Log Analytics query."),
    ToolProperty("ServerName", "string", "The name of the Windows Server to query"),
    ToolProperty("timespan", "string", "The timespan for the query (e.g., '30d' for 30 days)"),
]

# Convert agent function tool properties to JSON
tool_properties_subscription_id_json = json.dumps([prop.to_dict() for prop in tool_properties_subscription_id])
tool_properties_log_analytics_json = json.dumps([prop.to_dict() for prop in tool_properties_log_analytics])
tool_properties_log_analytics_with_server_json = json.dumps([prop.to_dict() for prop in tool_properties_log_analytics_with_server])


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetServerMetadata",
    description="Retrieve the server infrastructure configuration",
    toolProperties=tool_properties_subscription_id_json,
)
def get_server_metadata_function(context) -> str:
    """
    Azure Function wrapper for GetServerMetadata.
    
    Args:
        context: The trigger context containing the input arguments.
        
    Returns:
        str: JSON string with server metadata.
    """
    try:
        content = json.loads(context)
        subscription_id = content["arguments"]["subscription_id"]
        
        # Call the agent function
        result = GetServerMetadata(subscription_id)
        return result
    except Exception as e:
        logging.error(f"Error in get_server_metadata_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetSqlMetadata",
    description="Retrieve the SQL infrastructure configuration",
    toolProperties=tool_properties_subscription_id_json,
)
def get_sql_metadata_function(context) -> str:
    """
    Azure Function wrapper for GetSqlMetadata.
    
    Args:
        context: The trigger context containing the input arguments.
        
    Returns:
        str: JSON string with SQL metadata.
    """
    try:
        content = json.loads(context)
        subscription_id = content["arguments"]["subscription_id"]
        
        # Call the agent function
        result = GetSqlMetadata(subscription_id)
        return result
    except Exception as e:
        logging.error(f"Error in get_sql_metadata_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetPatchingLevel",
    description="Retrieve the missed patches list for the ServeName",
    toolProperties=tool_properties_subscription_id_json,
)
def get_patching_level_function(context) -> str:
    """
    Azure Function wrapper for GetPatchingLevel.
    
    Args:
        context: The trigger context containing the input arguments.
        
    Returns:
        str: JSON string with patching information.
    """
    try:
        content = json.loads(context)
        subscription_id = content["arguments"]["subscription_id"]
        
        # Call the agent function
        result = GetPatchingLevel(subscription_id)
        return result
    except Exception as e:
        logging.error(f"Error in get_patching_level_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetSqlBpAssessment",
    description="Retrieve the SQL Server best practices assessment",
    toolProperties=tool_properties_log_analytics_json,
)
def get_sql_bp_assessment_function(context) -> str:
    """
    Azure Function wrapper for GetSqlBpAssessment.
    
    Args:
        context: The trigger context containing the input arguments.
        
    Returns:
        str: JSON string with SQL best practices assessment.
    """
    try:
        content = json.loads(context)
        workspace_id = content["arguments"]["workspace_id"]
        timespan = content["arguments"].get("timespan")
        
        # Call the agent function
        result = GetSqlBpAssessment(workspace_id, timespan)
        return result
    except Exception as e:
        logging.error(f"Error in get_sql_bp_assessment_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetAnomalies",
    description="Detect anomalies on the metrics behavior for your servers",
    toolProperties=tool_properties_log_analytics_json,
)
def get_anomalies_function(context) -> str:
    """
    Azure Function wrapper for GetAnomalies.
    
    Args:
        context: The trigger context containing the input arguments.
        
    Returns:
        str: JSON string with detected anomalies.
    """
    try:
        content = json.loads(context)
        workspace_id = content["arguments"]["workspace_id"]
        timespan = content["arguments"].get("timespan")
        
        # Call the agent function
        result = GetAnomalies(workspace_id, timespan)
        return result
    except Exception as e:
        logging.error(f"Error in get_anomalies_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetSwChangesList",
    description="Find the software configuration changes for a specific server",
    toolProperties=tool_properties_log_analytics_with_server_json,
)
def get_sw_changes_list_function(context) -> str:
    """
    Azure Function wrapper for GetSwChangesList.
    
    Args:
        context: The trigger context containing the input arguments.
        
    Returns:
        str: JSON string with software configuration changes.
    """
    try:
        content = json.loads(context)
        workspace_id = content["arguments"]["workspace_id"]
        server_name = content["arguments"]["ServerName"]
        timespan = content["arguments"].get("timespan")
        
        # Call the agent function
        result = GetSwChangesList(workspace_id, server_name, timespan)
        return result
    except Exception as e:
        logging.error(f"Error in get_sw_changes_list_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetSwConfig",
    description="Find the software configuration for servers",
    toolProperties=tool_properties_log_analytics_with_server_json,
)
def get_sw_config_function(context) -> str:
    """
    Azure Function wrapper for GetSwConfig.
    
    Args:
        context: The trigger context containing the input arguments.
        
    Returns:
        str: JSON string with software configuration.
    """
    try:
        content = json.loads(context)
        workspace_id = content["arguments"]["workspace_id"]
        server_name = content["arguments"]["ServerName"]
        timespan = content["arguments"].get("timespan")
        
        # Call the agent function
        result = GetSwConfig(workspace_id, server_name, timespan)
        return result
    except Exception as e:
        logging.error(f"Error in get_sw_config_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetWinBpAssessment",
    description="Retrieve the Windows Server infrastructure issues and remediations",
    toolProperties=tool_properties_log_analytics_json,
)
def get_win_bp_assessment_function(context) -> str:
    """
    Azure Function wrapper for GetWinBpAssessment.
    
    Args:
        context: The trigger context containing the input arguments.
        
    Returns:
        str: JSON string with Windows best practices assessment.
    """
    try:
        content = json.loads(context)
        workspace_id = content["arguments"]["workspace_id"]
        timespan = content["arguments"].get("timespan")
        
        # Call the agent function
        result = GetWinBpAssessment(workspace_id, timespan)
        return result
    except Exception as e:
        logging.error(f"Error in get_win_bp_assessment_function: {str(e)}")
        return json.dumps({"error": str(e)})
