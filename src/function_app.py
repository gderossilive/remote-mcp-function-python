import json
import logging
import os

import azure.functions as func
from agent_functions import GetServerMetadata, GetSqlBpAssessment, GetSqlMetadata, GetPatchingLevel, GetAnomalies

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

# Constants for the Azure Blob Storage container, file, and blob path
_SNIPPET_NAME_PROPERTY_NAME = "snippetname"
_SNIPPET_PROPERTY_NAME = "snippet"
_BLOB_PATH = "snippets/{mcptoolargs." + _SNIPPET_NAME_PROPERTY_NAME + "}.json"


class ToolProperty:
    def __init__(self, property_name: str, property_type: str, description: str):
        self.propertyName = property_name
        self.propertyType = property_type
        self.description = description

    def to_dict(self):
        return {
            "propertyName": self.propertyName,
            "propertyType": self.propertyType,
            "description": self.description,
        }


# Define the tool properties using the ToolProperty class
tool_properties_save_snippets_object = [
    ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet."),
    ToolProperty(_SNIPPET_PROPERTY_NAME, "string", "The content of the snippet."),
]

tool_properties_get_snippets_object = [ToolProperty(_SNIPPET_NAME_PROPERTY_NAME, "string", "The name of the snippet.")]

# Convert the tool properties to JSON
tool_properties_save_snippets_json = json.dumps([prop.to_dict() for prop in tool_properties_save_snippets_object])
tool_properties_get_snippets_json = json.dumps([prop.to_dict() for prop in tool_properties_get_snippets_object])

# Tool properties for agent functions
tool_properties_subscription_ids = [
    ToolProperty("subscription_ids", "array", "List of Azure subscription IDs to query Azure Resource Manager against"),
]

tool_properties_log_analytics = [
    ToolProperty("workspace_id", "string", "The workspace ID for the Log Analytics query."),
    ToolProperty("timespan", "string", "The timespan for the query (e.g., '30d' for 30 days)"),
]

# Convert agent function tool properties to JSON
tool_properties_subscription_ids_json = json.dumps([prop.to_dict() for prop in tool_properties_subscription_ids])
tool_properties_log_analytics_json = json.dumps([prop.to_dict() for prop in tool_properties_log_analytics])


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="hello_mcp",
    description="Hello world.",
    toolProperties="[]",
)
def hello_mcp(context) -> None:
    """
    A simple function that returns a greeting message.

    Args:
        context: The trigger context (not used in this function).

    Returns:
        str: A greeting message.
    """
    return "Hello I am MCPTool!"


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_snippet",
    description="Retrieve a snippet by name.",
    toolProperties=tool_properties_get_snippets_json,
)
@app.generic_input_binding(arg_name="file", type="blob", connection="AzureWebJobsStorage", path=_BLOB_PATH)
def get_snippet(file: func.InputStream, context) -> str:
    """
    Retrieves a snippet by name from Azure Blob Storage.

    Args:
        file (func.InputStream): The input binding to read the snippet from Azure Blob Storage.
        context: The trigger context containing the input arguments.

    Returns:
        str: The content of the snippet or an error message.
    """
    snippet_content = file.read().decode("utf-8")
    logging.info(f"Retrieved snippet: {snippet_content}")
    return snippet_content


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="save_snippet",
    description="Save a snippet with a name.",
    toolProperties=tool_properties_save_snippets_json,
)
@app.generic_output_binding(arg_name="file", type="blob", connection="AzureWebJobsStorage", path=_BLOB_PATH)
def save_snippet(file: func.Out[str], context) -> str:
    content = json.loads(context)
    snippet_name_from_args = content["arguments"][_SNIPPET_NAME_PROPERTY_NAME]
    snippet_content_from_args = content["arguments"][_SNIPPET_PROPERTY_NAME]

    if not snippet_name_from_args:
        return "No snippet name provided"

    if not snippet_content_from_args:
        return "No snippet content provided"

    file.set(snippet_content_from_args)
    logging.info(f"Saved snippet: {snippet_content_from_args}")
    return f"Snippet '{snippet_content_from_args}' saved successfully"


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetServerMetadata",
    description="Retrieve the server infrastructure configuration",
    toolProperties=tool_properties_subscription_ids_json,
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
        subscription_ids = content["arguments"]["subscription_ids"]
        
        # Call the agent function
        result = GetServerMetadata(None, subscription_ids)
        return result
    except Exception as e:
        logging.error(f"Error in get_server_metadata_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetSqlMetadata",
    description="Retrieve the SQL infrastructure configuration",
    toolProperties=tool_properties_subscription_ids_json,
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
        subscription_ids = content["arguments"]["subscription_ids"]
        
        # Call the agent function
        result = GetSqlMetadata(None, subscription_ids)
        return result
    except Exception as e:
        logging.error(f"Error in get_sql_metadata_function: {str(e)}")
        return json.dumps({"error": str(e)})


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="GetPatchingLevel",
    description="Retrieve the missed patches list for the ServeName",
    toolProperties=tool_properties_subscription_ids_json,
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
        subscription_ids = content["arguments"]["subscription_ids"]
        
        # Call the agent function
        result = GetPatchingLevel(None, subscription_ids)
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
        result = GetSqlBpAssessment(None, workspace_id, timespan)
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
        result = GetAnomalies(None, workspace_id, timespan)
        return result
    except Exception as e:
        logging.error(f"Error in get_anomalies_function: {str(e)}")
        return json.dumps({"error": str(e)})
