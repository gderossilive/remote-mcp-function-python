#!/usr/bin/env python3
"""
MCP Tools for AI4Ops Server
Extracted from ai4ops_mcp_server.py
"""

import warnings
import sys
import os
import logging
import json
import pandas as pd
from typing import Annotated, List

# Early logging suppression check
if os.getenv('SUPPRESS_MCP_LOGGING', 'false').lower() == 'true':
    # Suppress this module and related modules immediately
    logging.getLogger(__name__).setLevel(logging.WARNING)
    logging.getLogger('utils.log_analytics_tool').setLevel(logging.WARNING)
    logging.getLogger('utils.resource_graph_tool').setLevel(logging.WARNING)
    logging.getLogger('utils.logging_decorators').setLevel(logging.WARNING)
    logging.getLogger('azure').setLevel(logging.WARNING)
    logging.getLogger('azure.identity').setLevel(logging.WARNING)
    logging.getLogger('azure.monitor').setLevel(logging.WARNING)

# Import utilities
from utils.logging_decorators import log_function_call
from utils.log_analytics_tool import LogAnalyticsTool
from utils.resource_graph_tool import ResourceGraphTool

# Add Azure Identity imports for credential handling
from azure.identity import DefaultAzureCredential, ManagedIdentityCredential, EnvironmentCredential, AzureCliCredential, ChainedTokenCredential

# Set up logging
logger = logging.getLogger(__name__)

# ----------------------------------------------------------
# Helper function for credential management


def get_credential():
    """
    Get the appropriate credential for Azure authentication with fallbacks.
    This function prioritizes user authentication methods over managed identity.

    Returns:
        An Azure credential object that can be used for authentication
    """
    logger.info("Attempting to create credential chain for Azure authentication")

    try:
        # Prioritize user authentication methods:
        # 1. Azure CLI credentials (user logged in)
        # 2. Environment variables (user-provided)
        # 3. Managed Identity as fallback
        credential = ChainedTokenCredential(
            AzureCliCredential(),
            EnvironmentCredential(),
            ManagedIdentityCredential()
        )
        logger.info("Successfully created user-prioritized credential chain")
        return credential
    except Exception as e:
        logger.warning(f"Failed to create credential chain: {str(e)}")
        logger.info("Falling back to DefaultAzureCredential with user auth priority")

        # If chained credential fails, try DefaultAzureCredential with user auth enabled
        try:
            credential = DefaultAzureCredential(exclude_managed_identity_credential=False)
            logger.info(
                "Successfully created DefaultAzureCredential with user auth priority")
            return credential
        except Exception as e2:
            logger.warning(
                f"Failed to create DefaultAzureCredential: {str(e2)}")

            # Last resort - try CLI only
            logger.info("Falling back to AzureCliCredential only")
            return AzureCliCredential()

# ----------------------------------------------------------
# Helper function to ensure objects are JSON serializable


def ensure_serializable(obj):
    """Recursively convert any non-serializable objects to serializable ones."""
    import pandas as pd
    import datetime

    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
    elif isinstance(obj, pd.Timestamp):
        # Convert pandas Timestamp objects to ISO format string
        return obj.isoformat()
    elif isinstance(obj, datetime.datetime):
        # Convert datetime objects to ISO format string
        return obj.isoformat()
    elif isinstance(obj, datetime.date):
        # Convert date objects to ISO format string
        return obj.isoformat()
    elif hasattr(obj, 'to_dict'):
        return obj.to_dict()
    elif hasattr(obj, '__dict__'):
        return {k: ensure_serializable(v) for k, v in obj.__dict__.items()}
    elif isinstance(obj, (list, tuple)):
        return [ensure_serializable(item) for item in obj]
    elif isinstance(obj, dict):
        return {k: ensure_serializable(v) for k, v in obj.items()}
    else:
        try:
            # Try to see if it's JSON serializable as-is
            json.dumps(obj)
            return obj
        except (TypeError, OverflowError):
            # If not serializable, convert to string
            return str(obj)


# ----------------------------------------------------------
# MCP Tools Functions
# Note: These functions need to be registered with an MCP server instance

@log_function_call
def resource_graph_tool(query: str, subscription_id: str = None):
    """Run a KQL query on Azure Resource Graph."""
    logger.debug(f"Running Resource Graph query: {query}")
    # sys.stderr.write("🔧 TOOL CALL: resource_graph_tool\n")
    # sys.stderr.flush()

    try:
        # If subscription_id not provided, use the one from environment variables
        if not subscription_id:
            subscription_id = os.getenv("SUBSCRIPTION_ID")
            logger.info(
                f"Using subscription ID from environment: {subscription_id}")

        # Convert single subscription_id to list for the ResourceGraphTool
        subscription_ids = [subscription_id]

        # Get the appropriate credential for the environment
        credential = get_credential()
        logger.debug("Obtained credential for Resource Graph query")

        # Create a new ResourceGraphTool instance with our credential
        graph_tool = ResourceGraphTool(credential=credential)
        logger.debug("Created ResourceGraphTool with credential")

        # Execute the query
        response = graph_tool.run_query(query, subscription_ids)
        logger.debug(f"Query response received with type: {type(response)}")

        # Make sure all objects are JSON serializable
        serializable_response = ensure_serializable(response)
        return json.dumps(serializable_response)
    except Exception as e:
        logger.error(f"Exception in resource_graph_tool: {str(e)}")
        return json.dumps({"error": str(e)})


@log_function_call
def log_analytics_tool(query: str, workspace_id: str, timespan: str = None):
    """
    Run a KQL query on Azure Log Analytics.

    Args:
        query (str): The KQL query to execute
        workspace_id (str): The Log Analytics workspace ID
        timespan (str, optional): The timespan for the query (e.g., "30d" for 30 days)

    Returns:
        str: JSON string with the results of the query
    """
    logger.debug(f"Running Log Analytics query on workspace: {workspace_id}")
    logger.debug(f"Query: {query}")

    # Log the tool call for telemetry
    # sys.stderr.write("🔧 TOOL CALL: log_analytics_tool\n")
    # sys.stderr.flush()

    # Use default timespan
    if not timespan:
        timespan = "30d"
        logger.info(f"Using default timespan: {timespan}")
    else:
        logger.info(f"Using provided timespan: {timespan}")

    try:
        # Get the appropriate credential for the environment
        credential = get_credential()
        logger.debug("Obtained credential for Log Analytics query")

        # Create a new LogAnalyticsTool instance with our credential
        analytics_tool = LogAnalyticsTool(credential=credential)
        logger.debug("Created LogAnalyticsTool with credential")

        # Execute the query
        response = analytics_tool.run_query(query, workspace_id, timespan)
        logger.info(f"Query response type: {type(response)}")
        logger.debug(f"Query response: {response}")

        # Make sure all objects are JSON serializable
        serializable_response = ensure_serializable(response)
        return json.dumps(serializable_response)
    except Exception as e:
        logger.error(f"Exception in log_analytics_tool: {str(e)}")
        return json.dumps({"error": str(e)})


@log_function_call
def GetPatchingLevel(subscription_id: str) -> str:
    """Retrieve the missed patches list by ServeName. This action provides the following metadata for missed patches: 
    Name, KB, Classification, Published Date, Reboot Behavior and Severity.

    Arguments:
    subscription_id (str): Azure subscription ID to query Azure Resource Manager against.

    Returns (str): 
    The list of the missing patch for all the virtual machines in the environment in JSON format.
    """
    # logger.info("GetServerMetadata: Starting to get the server metadata")
    logger.debug(f"GetPatchingLevel: Subscription ID: {subscription_id}")
    sys.stderr.write("🔧 TOOL CALL: GetPatchingLevel\n")
    sys.stderr.flush()

    # get the subscription ID from the environment variable
    # subscription_id = os.environ.get("SUBSCRIPTION_ID")

    # check if the subscription_id is provided
    if not subscription_id:
        logger.error("GetPatchingLevel: subscription_id is required")
        return json.dumps({"error": "subscription_id is required"})

    kql_query = "patchassessmentresources | where type == 'microsoft.hybridcompute/machines/patchassessmentresults/softwarepatches'| project ServerName= extract(@'/machines/([^/]+)/', 1, id), MissedPatch=properties"

    response = resource_graph_tool(kql_query, subscription_id)
    if not response:
        logger.error("GetPatchingLevel: No response from Resource Graph Tool")
        return json.dumps({"error": "No response from Resource Graph Tool"})

    logger.debug("GetPatchingLevel: Finished getting the server metadata")
    return response


@log_function_call
def GetSqlMetadata(subscription_id: str) -> str:
    """Retrieve the SQL infrastructure configuration. 
    The infrastructure is composed by SQL Servers/instances, every SQL Server/instance could have multiple SQL databases. 
    You are able to retrieve following metadata: Database name (DbName), SQL Server name (SrvName), cores used by the server (SrvvCore), 
    disk space used in MB by database (DbSizeMB), disk space in MB available for the database (DbSpaceAvailableMB), 
    license version used (SrvVersion), license type used (SrvLicenseType), license edition used (SrvEdition), 
    information about database backup (DbBackupInformation).

    Arguments:
    subscription_id (str): Azure subscription ID to query Azure Resource Manager against.

    Returns (str): 
    SQL infrastructure configuration is composed by the following metadata: Database name (DbName), 
    SQL Server name (SrvName), cores used by the server (SrvvCore), disk space used in MB by database (DbSizeMB), 
    disk space in MB available for the database (DbSpaceAvailableMB), license version used (SrvVersion), 
    license type used (SrvLicenseType), license edition used (SrvEdition), 
    information about database backup (DbBackupInformation) in JSON format.
    """
    # logger.info("GetServerMetadata: Starting to get the server metadata")
    logger.debug(f"GetSqlMetadata: Subscription ID: {subscription_id}")
    sys.stderr.write("🔧 TOOL CALL: GetSqlMetadata\n")
    sys.stderr.flush()

    # get the subscription ID from the environment variable
    # subscription_id = os.environ.get("SUBSCRIPTION_ID")

    # check if the subscription_id is provided
    if not subscription_id:
        logger.error("GetSqlMetadata: subscription_id is required")
        return json.dumps({"error": "subscription_id is required"})

    kql_query = "resources | where type =~ 'microsoft.azurearcdata/sqlserverinstances' | project id, SrvName=name, SrvVersion=tostring(properties['version']), SrvLicenseType=tostring(properties['licenseType']), SrvEdition=tostring(properties['edition']), SrvvCore=toint(properties['vCore']) | join kind=leftouter (resources | where type =~'microsoft.azurearcdata/sqlserverinstances/databases' | project id,DbName=name, DatabaseOptions=properties['databaseOptions'], DbBackupInformation=properties['backupInformation'],DbSpaceAvailableMB=toint(properties['spaceAvailableMB']), DbSizeMB=toint(properties['sizeMB']) | extend ServerId=tostring(parse_path(tostring(parse_path(['id'])['DirectoryPath'])) ['DirectoryPath']) ) on $left.id == $right.ServerId | project-away id, id1"

    response = resource_graph_tool(kql_query, subscription_id)
    if not response:
        logger.error("GetSqlMetadata: No response from Resource Graph Tool")
        return json.dumps({"error": "No response from Resource Graph Tool"})

    logger.debug("GetSqlMetadata: Finished getting the server metadata")
    return response


@log_function_call
def GetServerMetadata(subscription_id: str) -> str:
    """Retrieve the server infrastructure configuration. 
    The infrastructure could be composed by Windows Servers and/or Linux Servers. 
    You are able to retrieve following metadata: Server name (name), hybrid or native Azure server (type), 
    geographical location or data center where the server is hosted (location), operative system version (OsVersion), 
    type and model of the CPU (processor), number of CPU cores (coreCount), amount of memory (RAM) installed (RamGB), 
    subnet used by vm (subnet), Whether SQL Server is installed on the server (mssqlDiscovered). 

    Arguments:
        subscription_id (str): Azure subscription ID to query Azure Resource Manager against.

    Returns (str): 
        The server infrastructure configuration is composed by the following metadata: Server name (name), 
        hybrid or native Azure server (type), Azure region (location), operative system version (OsVersion), 
        processor used by vm (processor), core count used by vm (coreCount), RAM used by VM in GB (RamGB), 
        subnet used by vm (subnet), if SQL is installed on vm (mssqlDiscovered) in JSON format.
    """
    # logger.info("GetServerMetadata: Starting to get the server metadata")
    logger.debug(f"GetServerMetadata: Subscription ID: {subscription_id}")
    sys.stderr.write("🔧 TOOL CALL: GetServerMetadata\n")
    sys.stderr.flush()
    logger.info("TOOL: GetServerMetadata", extra={
                'tool_name': 'GetServerMetadata', 'component': 'mcp_tools'})
    # print(f"[TOOL Used] GetServerMetadata")
    # logger.error(f"[TOOL Used] GetServerMetadata")

    # get the subscription ID from the environment variable
    # subscription_id = os.environ.get("SUBSCRIPTION_ID")

    # check if the subscription_id is provided
    if not subscription_id:
        logger.error("GetServerMetadata: subscription_id is required")
        return json.dumps({"error": "subscription_id is required"})

    kql_query = "resources | where type == 'microsoft.hybridcompute/machines' | project name, type, location, resourceGroup, OsVersion=properties.osSku, processor=properties.detectedProperties.processorNames , coreCount=properties.detectedProperties.logicalCoreCount, RamGB=properties.detectedProperties.totalPhysicalMemoryInGigabytes, subnet=properties.networkProfile.networkInterfaces[0].ipAddresses[0].address, mssqlDiscovered=properties.mssqlDiscovered"

    response = resource_graph_tool(kql_query, subscription_id)
    if not response:
        logger.error("GetServerMetadata: No response from Resource Graph Tool")
        return json.dumps({"error": "No response from Resource Graph Tool"})

    logger.debug("GetServerMetadata: Finished getting the server metadata")
    return response


@log_function_call
def GetSqlBpAssessment(workspace_id: str, timespan: str = None) -> str:
    """Retrieves SQL Server Best Practices Assessment data from Azure Log Analytics."""
    logger.info(f"GetSqlBpAssessment: Workspace ID: {workspace_id}")
    logger.info(
        f"GetSqlBpAssessment: Executing query with timespan: {timespan}")
    sys.stderr.write("🔧 TOOL CALL: GetSqlBpAssessment\n")
    sys.stderr.flush()

    # Set default timespan if not provided
    if not timespan:
        timespan = "30d"

    # Construct the query with proper timespan handling
    query = f"let selectedCategories = dynamic([]);let selectedTotSev = dynamic([]); SqlAssessment_CL| where TimeGenerated > ago({timespan}) | extend asmt = parse_csv(RawData) | where asmt[11] =~ 'MSSQLSERVER' | extend AsmtId=tostring(asmt[1]), CheckId=tostring(asmt[2]), DisplayString=asmt[3], Description=tostring(asmt[4]), HelpLink=asmt[5], TargetType=case(asmt[6] == 1, 'Server', asmt[6] == 2, 'Database', ''), TargetName=tostring(asmt[7]), Severity=case(asmt[8] == 30, 'High', asmt[8] == 20, 'Medium', asmt[8] == 10, 'Low', asmt[8] == 0, 'Information', asmt[8] == 1, 'Warning', asmt[8] == 2, 'Critical', 'Passed'), Message=tostring(asmt[9]), TagsArr=split(tostring(asmt[10]), ','), Sev = toint(asmt[8]) | where (set_has_element(dynamic(['*']), CheckId) or '*' == '*') and (set_has_element(dynamic(['*']), TargetName) or '*' == '*') and set_has_element(dynamic([30, 20, 10, 0]), Sev) and (array_length(set_intersect(TagsArr, dynamic(['*']))) > 0 or '*' == '*') and (CheckId == '' and Sev == 0 or '' == '') | extend Category = case(array_length(set_intersect(TagsArr, dynamic(['CPU', 'IO', 'Storage']))) > 0, '0', array_length(set_intersect(TagsArr, dynamic(['TraceFlag', 'Backup', 'DBCC', 'DBConfiguration', 'SystemHealth', 'Traces', 'DBFileConfiguration', 'Configuration', 'Replication', 'Agent', 'Security', 'DataIntegrity', 'MaxDOP', 'PageFile', 'Memory', 'Performance', 'Statistics']))) > 0, '1', array_length(set_intersect(TagsArr, dynamic(['UpdateIssues', 'Index', 'Naming', 'Deprecated', 'masterDB', 'QueryOptimizer', 'QueryStore', 'Indexes']))) > 0, '2', '3') | where (Sev >= 0 and array_length(selectedTotSev) == 0 or Sev in (selectedTotSev)) and (Category in (selectedCategories) or array_length(selectedCategories) == 0) | project TargetType, TargetName, Severity, Message, Tags=strcat_array(array_slice(TagsArr, 1, -1), ', '), CheckId, Description, HelpLink = tostring(HelpLink), SeverityCode = toint(Sev) | order by SeverityCode desc, TargetType desc, TargetName asc | project-away SeverityCode | extend PackedRecord = pack_all() | summarize Result = make_list(PackedRecord)"

    try:
        # Pass None for timespan since we've embedded it in the query
        return log_analytics_tool(query, workspace_id, None)
    except Exception as e:
        logger.error(f"Error in GetSqlBpAssessment: {str(e)}")
        return json.dumps({"error": str(e)})


@log_function_call
def GetSwChangesList(workspace_id: str, ServerName: str, timespan: str = None) -> str:
    """Use this tool when you need to find the software configuration changes for a specific server. Using this tool you get: 
    name of the software (SoftwareName), who publisehd/produced the software (Publisher), the name of the server using this software (Computer), 
    the time stamp when this information has been assessed (TimeGenerated), which kind of software it is (SoftwareType), the type of the change occured (ChangeCategory), the previous state of this software (Previous)

    Arguments:
        workspace_id (str): The workspace ID for the Log Analytics query
        ServerName (str): The name of the Windows Server to query
        timespan (str, optional): The timespan for the query (e.g., "30d" for 30 days)       
    Returns (str):
        The list of the software configuration changes for a specific server in JSON format
    """
    logger.info(f"GetSwChangesList: Workspace ID: {workspace_id}")
    logger.info(f"GetSwChangesList: Executing query with timespan: {timespan}")
    sys.stderr.write("🔧 TOOL CALL: GetSwChangesList\n")
    sys.stderr.flush()

    # Set default timespan if not provided
    if not timespan:
        timespan = "30d"
        logger.info(
            f"GetSwChangesList: No timespan provided, using default: {timespan}")

    # Use default tool configuration
    max_results = 500
    include_system_changes = False

    # Build system change filter
    system_filter = ""
    if not include_system_changes:
        system_filter = "| where SoftwareType !in ('Security Update', 'Update', 'Hotfix')"

    # Construct the optimized query with proper time filtering and result limiting
    query = f"""ConfigurationChange 
| where TimeGenerated > datetime_utc_to_local(now(2h)-{timespan}, 'Europe/Rome') 
| where ConfigChangeType == 'Software' and Computer == '{ServerName}'
{system_filter}
| project TimeGenerated, Computer, ChangeCategory, SoftwareType, SoftwareName, Previous, Publisher
| top {max_results} by TimeGenerated desc"""

    logger.info(
        f"GetSwChangesList: Query optimized with timespan {timespan} and max results {max_results}")

    try:
        # Pass None for timespan since we've embedded it in the query
        return log_analytics_tool(query, workspace_id, None)
    except Exception as e:
        logger.error(f"Error in GetSwChangesList: {str(e)}")
        return json.dumps({"error": str(e)})


@log_function_call
def GetSwConfig(workspace_id: str, ServerName: str, timespan: str = None) -> str:
    """Use this tool when you need to find the software configuration for servers. 
    Using this tool you get: name of the software (SoftwareName), who publisehd/produced the software (Publisher), 
    the name of the server using this software (Computer), the time stamp when this information has been assessed (TimeGenerated), 
    which kind of software it is (SoftwareType) and the version of the software (CurrentVersion)    
    Arguments:
        workspace_id (str): The workspace ID for the Log Analytics query
        ServerName (str): The name of the Windows Server to query
        timespan (str, optional): The timespan for the query (e.g., "30d" for 30 days)        
    Returns (str):
        The chronological list of the software installed in JSON format
    """
    logger.info(f"GetSwConfig: Workspace ID: {workspace_id}")
    logger.info(f"GetSwConfig: Executing query with timespan: {timespan}")
    sys.stderr.write("🔧 TOOL CALL: GetSwConfig\n")
    sys.stderr.flush()

    # Set default timespan if not provided
    if not timespan:
        timespan = "30d"
        logger.info(
            f"GetSwConfig: No timespan provided, using default: {timespan}")

    # Use default tool configuration
    max_results = 1000
    include_system_software = False

    # Build the optimized query with proper time filtering and result limiting
    system_filter = ""
    if not include_system_software:
        system_filter = "| where SoftwareType !in ('Security Update', 'Update', 'Hotfix', 'Definition Update')"

    query = f"""ConfigurationData 
| where TimeGenerated > ago({timespan})
| where Computer == '{ServerName}' and SoftwareName != '' and SoftwareName !~ 'unknown'
{system_filter}
| summarize arg_max(TimeGenerated, *) by SoftwareName, Publisher, Computer, SoftwareType, CurrentVersion
| project SoftwareName, Publisher, Computer, TimeGenerated, SoftwareType, CurrentVersion
| top {max_results} by SoftwareName asc"""

    logger.info(
        f"GetSwConfig: Query optimized with timespan {timespan} and max results {max_results}")

    try:
        # Pass None for timespan since we've embedded it in the query
        return log_analytics_tool(query, workspace_id, None)
    except Exception as e:
        logger.error(f"Error in GetSwConfig: {str(e)}")
        return json.dumps({"error": str(e)})


@log_function_call
def GetWinBpAssessment(workspace_id: str, timespan: str = None) -> str:
    """Retrieve the Windows Server infrastructure issues and remediations. IT can retrieves: the name of the Windows Server (Computer), 
    Description of the recommendation (Recommendation), which area is impacted (ActionArea), if the server or the cluster is impacted (AffectedObjectType), 
    type of remediation (FocusArea), Description of the recommendation (Description), the score assigned to the severity of the issue (Weight)

    Arguments:
        workspace_id (str): The workspace ID for the Log Analytics query
        timespan (str, optional): The timespan for the query (e.g., "30d" for 30 days)
    Returns (str):
        The Windows infrastructure configuration with remediation recommendations in JSON format
    """
    logger.info(f"GetWinBpAssessment: Workspace ID: {workspace_id}")
    logger.info(
        f"GetWinBpAssessment: Executing query with timespan: {timespan}")
    sys.stderr.write("🔧 TOOL CALL: GetWinBpAssessment\n")
    sys.stderr.flush()

    # Use default tool configuration
    weight_threshold = 5.0
    max_results = 500

    # Set default timespan if not provided
    if not timespan:
        timespan = "30d"
        logger.info(
            f"GetWinBpAssessment: No timespan provided, using default: {timespan}")
    else:
        logger.info(f"GetWinBpAssessment: Using provided timespan: {timespan}")

    # Construct the optimized query with proper time filtering and result limiting
    query = f"""WindowsServerAssessmentRecommendation 
| where TimeGenerated > ago({timespan})
| where FocusArea != 'EnvironementFilter' and RecommendationResult == 'Failed' and Computer != ''
| extend Weight = (RecommendationScore/10)
| where Weight >= {weight_threshold}
| summarize by Computer, Recommendation, ActionArea, AffectedObjectType, FocusArea, RecommendationId, Description, Weight
| top {max_results} by Weight desc"""

    logger.info(
        f"GetWinBpAssessment: Query optimized with timespan {timespan}, weight threshold {weight_threshold}, and max results {max_results}")

    try:
        # Pass None for timespan since we've embedded it in the query
        return log_analytics_tool(query, workspace_id, None)
    except Exception as e:
        logger.error(f"Error in GetWinBpAssessment: {str(e)}")
        return json.dumps({"error": str(e)})


@log_function_call
def GetAnomalies(workspace_id: str, timespan: str = None) -> str:
    """
    Use this tool to detect anomalies on the metrics behavior of your servers. 
    The metrics analyzed are "Processor" and "Logical Disk"

    Arguments:
        workspace_id (str): The workspace ID for the Log Analytics query.
        timespan (str): The timespan for the query (e.g., "30d" for 30 days).


    :return: 
    The list of anomalies detected on servers. Every anomaly has the following details: 
    date and time when the anomaly occurred (TimeGenerated), server where the anomaly occured (Computer), 
    the metrics experieced the anomaly (Namespace), the usage measured (ActualUsage), 
    the usage expected (ExpectedUsage) and a KPI named AnomalyScore which measure how much the anomaly is critical (higher means more critical)
    """

    logger.info(f"GetAnomalies: Workspace ID: {workspace_id}")
    sys.stderr.write("🔧 TOOL CALL: GetAnomalies\n")
    sys.stderr.flush()

    # Use default tool configuration
    anomaly_threshold = 10.0
    metrics = ["Processor", "LogicalDisk"]
    include_expected = True

    # Set default timespan if not provided
    if not timespan:
        timespan = "30d"
        logger.info(
            f"GetAnomalies: No timespan provided, using default: {timespan}")
    else:
        logger.info(f"GetAnomalies: Using provided timespan: {timespan}")

    # Build metrics filter based on configuration
    metrics_filter = " or ".join(
        [f"Namespace == '{metric}'" for metric in metrics])

    # Build the query with configurable parameters - simplified to avoid validation issues
    query = f"""InsightsMetrics 
| where TimeGenerated >= ago({timespan})
| where Namespace in ('Processor', 'LogicalDisk')
| where isnotempty(Val) and isfinite(Val)
| summarize AvgValue = avg(Val) by Computer, Namespace, bin(TimeGenerated, 1h)
| where AvgValue > 80
| project TimeGenerated, Computer, Namespace, AvgValue
| sort by AvgValue desc
| take 100"""

    logger.info(f"GetAnomalies: Executing query with timespan: {timespan}")
    logger.info(f"GetAnomalies: Using anomaly threshold: {anomaly_threshold}")
    logger.info(f"GetAnomalies: Monitoring metrics: {metrics}")
    logger.info(f"GetAnomalies: Workspace ID: {workspace_id}")

    # Pass None for timespan since we've embedded it in the query
    response = log_analytics_tool(query, workspace_id, None)
    if not response:
        logger.error("GetAnomalies: No response from Log Analytics Tool")
        return json.dumps({"error": "No response from Log Analytics Tool"})

    return response


# ----------------------------------------------------------
# Tool Registration Function


def register_tools_with_mcp(mcp_instance):
    """
    Register all MCP tools with the provided MCP server instance.

    Args:
        mcp_instance: The FastMCP server instance to register tools with
    """

    # Register the basic tools
    mcp_instance.tool()(resource_graph_tool)
    mcp_instance.tool()(log_analytics_tool)

    # Register the specialized tools
    mcp_instance.tool()(GetPatchingLevel)
    mcp_instance.tool()(GetSqlMetadata)
    mcp_instance.tool()(GetServerMetadata)
    mcp_instance.tool()(GetSqlBpAssessment)
    mcp_instance.tool()(GetSwChangesList)
    mcp_instance.tool()(GetSwConfig)
    mcp_instance.tool()(GetWinBpAssessment)
    mcp_instance.tool()(GetAnomalies)

    logger.info("All MCP tools registered successfully")


# ----------------------------------------------------------
# For standalone testing or import verification

if __name__ == "__main__":
    print("MCP Tools module loaded successfully")
    print("Available tools:")
    print("- resource_graph_tool")
    print("- log_analytics_tool")
    print("- GetPatchingLevel")
    print("- GetSqlMetadata")
    print("- GetServerMetadata")
    print("- GetSqlBpAssessment")
    print("- GetSwChangesList")
    print("- GetSwConfig")
    print("- GetWinBpAssessment")
    print("- GetAnomalies")
