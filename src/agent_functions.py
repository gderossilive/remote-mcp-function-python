import functools, logging, os, json
import pandas as pd

from utils.resource_graph_tool import ResourceGraphTool
from utils.log_analytics_tool import LogAnalyticsTool
from typing import Callable, Set, Any, List
from utils.logging_decorators import log_function_call

# Create module-specific logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# Define a decorator for function schemas
def function_schema(schema_dict):
    """Decorator to attach schema information to a function."""
    def decorator(func):
        func.__schema__ = schema_dict
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Helper function to ensure objects are JSON serializable
def ensure_serializable(obj):
    """Recursively convert any non-serializable objects to serializable ones."""
    if isinstance(obj, pd.DataFrame):
        return obj.to_dict(orient="records")
    elif isinstance(obj, (pd.Series, pd.Index)):
        return obj.tolist()
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

@log_function_call
def resource_graph_tool(self, query: str, subscription_ids: List[str] = None):
    """Run a KQL query on Azure Resource Graph."""
    logger.debug(f"Running Resource Graph query: {query}")
    
    try:
        # If subscription_ids not provided, use the one from environment variables
        if not subscription_ids:
            subscription_ids = [os.getenv("SUBSCRIPTION_ID")]
            
        # Create a new ResourceGraphTool instance
        graph_tool = ResourceGraphTool()
        
        # Execute the query
        response = graph_tool.run_query(query, subscription_ids)
        logger.debug(f"Query response received with type: {type(response)}")
        
        # Make sure all objects are JSON serializable
        serializable_response = ensure_serializable(response)
        return json.dumps(serializable_response)
    except Exception as e:
        logger.error(f"Exception in resource_graph_tool: {str(e)}")
        return json.dumps({"error": str(e)})

@log_function_call  # Applying logging decorator
def log_analytics_tool(self, query: str, workspace_id: str, timespan: str = None):
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
    if timespan:
        logger.info(f"Using timespan: {timespan}")
    else:
        logger.info("No timespan provided, using default")
    
    try:
        # Create a new LogAnalyticsTool instance
        analytics_tool = LogAnalyticsTool()
        
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

@function_schema({
    "name": "GetPatchingLevel",
    "description": "Retrieve the missed patches list for the ServeName",
    "parameters": {
        "type": "object",
        "properties": {
            "subscription_ids": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of Azure subscription IDs to query Azure Resource Manager against"
            }
        },
        "required": [
            "subscription_ids"
        ]
    }
})
@log_function_call  # Applying logging decorator
def GetPatchingLevel(self, subscription_ids) -> str:
    """Retrieve the missed patches list by ServeName. This action provides the following metadata for missed patches: 
    Name, KB, Classification, Published Date, Reboot Behavior and Severity.

    Arguments:
    subscription_ids (List[str]): List of Azure subscription IDs to query Azure Resource Manager against.

    Returns (str): 
    The list of the missing patch for all the virtual machines in the environment in JSON format.
    """
    #logger.info("GetServerMetadata: Starting to get the server metadata")
    logger.debug(f"GetPatchingLevel: Subscription IDs: {subscription_ids}")

    # get the subscription ID from the environment variable
    #subscription_id = os.environ.get("SUBSCRIPTION_ID")

    # check if the subscription_ids is different from None or a List
    if isinstance(subscription_ids, str):
        logger.info("GetPatchingLevel: subscription_ids is a string, converting to list")
        subscription_ids = [subscription_ids]
    elif isinstance(subscription_ids, list):
        logger.info("GetPatchingLevel: subscription_ids is a list")
    else:
        logger.error("GetPatchingLevel: subscription_ids is not a string or a list")
        return json.dumps({"error": "subscription_ids is not a string or a list"})
        

    kql_query = "patchassessmentresources | where type == 'microsoft.hybridcompute/machines/patchassessmentresults/softwarepatches'| project ServerName= extract(@'/machines/([^/]+)/', 1, id), MissedPatch=properties"

    response=resource_graph_tool(self, kql_query, subscription_ids)
    if not response:
        logger.error("GetPatchingLevel: No response from Resource Graph Tool")
        return json.dumps({"error": "No response from Resource Graph Tool"})
    
    logger.debug("GetPatchingLevel: Finished getting the server metadata")
    return response

@function_schema({
    "name": "GetSqlMetadata",
    "description": "Retrieve the SQL infrastructure configuration",
    "parameters": {
        "type": "object",
        "properties": {
            "subscription_ids": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of Azure subscription IDs to query Azure Resource Manager against"
            }
        },
        "required": [
            "subscription_ids"
        ]
    }
})
@log_function_call  # Applying logging decorator
def GetSqlMetadata(self, subscription_ids) -> str:
    """Retrieve the SQL infrastructure configuration. 
    The infrastructure is composed by SQL Servers/instances, every SQL Server/instance could have multiple SQL databases. 
    You are able to retrieve following metadata: Database name (DbName), SQL Server name (SrvName), cores used by the server (SrvvCore), 
    disk space used in MB by database (DbSizeMB), disk space in MB available for the database (DbSpaceAvailableMB), 
    license version used (SrvVersion), license type used (SrvLicenseType), license edition used (SrvEdition), 
    information about database backup (DbBackupInformation).

    Arguments:
    subscription_ids (List[str]): List of Azure subscription IDs to query Azure Resource Manager against.

    Returns (str): 
    SQL infrastructure configuration is composed by the following metadata: Database name (DbName), 
    SQL Server name (SrvName), cores used by the server (SrvvCore), disk space used in MB by database (DbSizeMB), 
    disk space in MB available for the database (DbSpaceAvailableMB), license version used (SrvVersion), 
    license type used (SrvLicenseType), license edition used (SrvEdition), 
    information about database backup (DbBackupInformation) in JSON format.
    """
    #logger.info("GetServerMetadata: Starting to get the server metadata")
    logger.debug(f"GetSqlMetadata: Subscription IDs: {subscription_ids}")

    # get the subscription ID from the environment variable
    #subscription_id = os.environ.get("SUBSCRIPTION_ID")

    # check if the subscription_ids is different from None or a List
    if isinstance(subscription_ids, str):
        logger.info("GetSqlMetadata: subscription_ids is a string, converting to list")
        subscription_ids = [subscription_ids]
    elif isinstance(subscription_ids, list):
        logger.info("GetSqlMetadata: subscription_ids is a list")
    else:
        logger.error("GetSqlMetadata: subscription_ids is not a string or a list")
        return json.dumps({"error": "subscription_ids is not a string or a list"})
        

    kql_query = "resources | where type =~ 'microsoft.azurearcdata/sqlserverinstances' | project id, SrvName=name, SrvVersion=tostring(properties['version']), SrvLicenseType=tostring(properties['licenseType']), SrvEdition=tostring(properties['edition']), SrvvCore=toint(properties['vCore']) | join kind=leftouter (resources | where type =~'microsoft.azurearcdata/sqlserverinstances/databases' | project id,DbName=name, DatabaseOptions=properties['databaseOptions'], DbBackupInformation=properties['backupInformation'],DbSpaceAvailableMB=toint(properties['spaceAvailableMB']), DbSizeMB=toint(properties['sizeMB']) | extend ServerId=tostring(parse_path(tostring(parse_path(['id'])['DirectoryPath'])) ['DirectoryPath']) ) on $left.id == $right.ServerId | project-away id, id1"

    response=resource_graph_tool(self, kql_query, subscription_ids)
    if not response:
        logger.error("GetSqlMetadata: No response from Resource Graph Tool")
        return json.dumps({"error": "No response from Resource Graph Tool"})
    
    logger.debug("GetSqlMetadata: Finished getting the server metadata")
    return response

# Apply schema using decorator
@function_schema({
    "name": "GetServerMetadata",
    "description": "Retrieve the server infrastructure configuration",
    "parameters": {
        "type": "object",
        "properties": {
            "subscription_ids": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of Azure subscription IDs to query Azure Resource Manager against"
            }
        },
        "required": [
            "subscription_ids"
        ]
    }
})
@log_function_call  # Applying logging decorator
def GetServerMetadata(self, subscription_ids) -> str:
    """Retrieve the server infrastructure configuration. 
    The infrastructure could be composed by Windows Servers and/or Linux Servers. 
    You are able to retrieve following metadata: Server name (name), hybrid or native Azure server (type), 
    geographical location or data center where the server is hosted (location), operative system version (OsVersion), 
    type and model of the CPU (processor), number of CPU cores (coreCount), amount of memory (RAM) installed (RamGB), 
    subnet used by vm (subnet), Whether SQL Server is installed on the server (mssqlDiscovered). 

    Arguments:
        subscription_ids (List[str]): List of Azure subscription IDs to query Azure Resource Manager against.

    Returns (str): 
        The server infrastructure configuration is composed by the following metadata: Server name (name), 
        hybrid or native Azure server (type), Azure region (location), operative system version (OsVersion), 
        processor used by vm (processor), core count used by vm (coreCount), RAM used by VM in GB (RamGB), 
        subnet used by vm (subnet), if SQL is installed on vm (mssqlDiscovered) in JSON format.
    """
    #logger.info("GetServerMetadata: Starting to get the server metadata")
    logger.debug(f"GetServerMetadata: Subscription IDs: {subscription_ids}")

    # get the subscription ID from the environment variable
    #subscription_id = os.environ.get("SUBSCRIPTION_ID")

    # check if the subscription_ids is different from None or a List
    if isinstance(subscription_ids, str):
        logger.info("GetServerMetadata: subscription_ids is a string, converting to list")
        subscription_ids = [subscription_ids]
    elif isinstance(subscription_ids, list):
        logger.info("GetServerMetadata: subscription_ids is a list")
    else:
        logger.error("GetServerMetadata: subscription_ids is not a string or a list")
        return json.dumps({"error": "subscription_ids is not a string or a list"})
        

    kql_query = "resources | where type == 'microsoft.hybridcompute/machines' | project name, type, location, resourceGroup, OsVersion=properties.osSku, processor=properties.detectedProperties.processorNames , coreCount=properties.detectedProperties.logicalCoreCount, RamGB=properties.detectedProperties.totalPhysicalMemoryInGigabytes, subnet=properties.networkProfile.networkInterfaces[0].ipAddresses[0].address, mssqlDiscovered=properties.mssqlDiscovered"

    response=resource_graph_tool(self, kql_query, subscription_ids)
    if not response:
        logger.error("GetServerMetadata: No response from Resource Graph Tool")
        return json.dumps({"error": "No response from Resource Graph Tool"})
    
    logger.debug("GetServerMetadata: Finished getting the server metadata")
    return response

@function_schema({
    "name": "GetSqlBpAssessment",
    "description": "Retrieve the SQL Server best practices assessment",
    "parameters": {
        "type": "object",
        "properties": {
            "workspace_id": {
                "type": "string",
                "description": "The workspace ID for the Log Analytics query."
            },
            "timespan": {
                "type": "string",
                "description": "The timespan for the query (e.g., '30d' for 30 days)"
            }
        },
        "required": ["workspace_id"]
    }
})
@log_function_call
def GetSqlBpAssessment(self, workspace_id: str, timespan: str = None) -> str:
    """Retrieves SQL Server Best Practices Assessment data from Azure Log Analytics."""
    logger.info(f"GetSqlBpAssessment: Workspace ID: {workspace_id}")
    logger.info(f"GetSqlBpAssessment: Executing query with timespan: {timespan}")
    
    # Construct the query - add your specific query here
    query = f"let selectedCategories = dynamic([]);let selectedTotSev = dynamic([]); SqlAssessment_CL| where TimeGenerated > (now()-{timespan}) | extend asmt = parse_csv(RawData) | where asmt[11] =~ 'MSSQLSERVER' | extend AsmtId=tostring(asmt[1]), CheckId=tostring(asmt[2]), DisplayString=asmt[3], Description=tostring(asmt[4]), HelpLink=asmt[5], TargetType=case(asmt[6] == 1, 'Server', asmt[6] == 2, 'Database', ''), TargetName=tostring(asmt[7]), Severity=case(asmt[8] == 30, 'High', asmt[8] == 20, 'Medium', asmt[8] == 10, 'Low', asmt[8] == 0, 'Information', asmt[8] == 1, 'Warning', asmt[8] == 2, 'Critical', 'Passed'), Message=tostring(asmt[9]), TagsArr=split(tostring(asmt[10]), ','), Sev = toint(asmt[8]) | where (set_has_element(dynamic(['*']), CheckId) or '*' == '*') and (set_has_element(dynamic(['*']), TargetName) or '*' == '*') and set_has_element(dynamic([30, 20, 10, 0]), Sev) and (array_length(set_intersect(TagsArr, dynamic(['*']))) > 0 or '*' == '*') and (CheckId == '' and Sev == 0 or '' == '') | extend Category = case(array_length(set_intersect(TagsArr, dynamic(['CPU', 'IO', 'Storage']))) > 0, '0', array_length(set_intersect(TagsArr, dynamic(['TraceFlag', 'Backup', 'DBCC', 'DBConfiguration', 'SystemHealth', 'Traces', 'DBFileConfiguration', 'Configuration', 'Replication', 'Agent', 'Security', 'DataIntegrity', 'MaxDOP', 'PageFile', 'Memory', 'Performance', 'Statistics']))) > 0, '1', array_length(set_intersect(TagsArr, dynamic(['UpdateIssues', 'Index', 'Naming', 'Deprecated', 'masterDB', 'QueryOptimizer', 'QueryStore', 'Indexes']))) > 0, '2', '3') | where (Sev >= 0 and array_length(selectedTotSev) == 0 or Sev in (selectedTotSev)) and (Category in (selectedCategories) or array_length(selectedCategories) == 0) | project TargetType, TargetName, Severity, Message, Tags=strcat_array(array_slice(TagsArr, 1, -1), ', '), CheckId, Description, HelpLink = tostring(HelpLink), SeverityCode = toint(Sev) | order by SeverityCode desc, TargetType desc, TargetName asc | project-away SeverityCode | extend PackedRecord = pack_all() | summarize Result = make_list(PackedRecord)"
    
    try:
        # The log_analytics_tool function now handles the DataFrame conversion
        return log_analytics_tool(self, query, workspace_id, timespan)
    except Exception as e:
        logger.error(f"Error in GetSqlBpAssessment: {str(e)}")
        return json.dumps({"error": str(e)})

@function_schema({
    "name": "GetAnomalies",
    "description": "Detect anomalies on the metrics behavior for your servers",
    "parameters": {
        "type": "object",
        "properties": {
            "workspace_id": {
                "type": "string",
                "description": "The workspace ID for the Log Analytics query."
            },
            "timespan": {
                "type": "string",
                "description": "The timespan for the query (e.g., '30d' for 30 days)"
            }
        },
        "required": ["workspace_id"]
    }
})
@log_function_call  # Applying logging decorator
def GetAnomalies(self, workspace_id: str, timespan: str = None) -> str:
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

    # LAW Name: LA-i0xi06
    #workspace_id = '93819b8e-f60e-40cf-8b96-9c9113b2b97e'

    if not timespan:
        logger.info("GetAnomalies: No timespan provided, using default of last 7 days")
        # Default to last 7 days   
        timespan = "7d"

    query = f"let starttime = {timespan}; let endtime = 0d; let timeframe = 30m; InsightsMetrics | where Namespace == 'Processor' or Namespace == 'LogicalDisk' | project TimeGenerated, Computer, Val, Namespace | summarize sum(Val) by bin(TimeGenerated, 5m), Computer, Namespace | make-series ActualUsage=avg(sum_Val) default = 0 on TimeGenerated from startofday(ago(starttime)) to startofday(ago(endtime)) step timeframe by Computer, Namespace | extend(Anomalies, AnomalyScore, ExpectedUsage) = series_decompose_anomalies(ActualUsage) | mv-expand ActualUsage to typeof(double), TimeGenerated to typeof(datetime), Anomalies to typeof(double),AnomalyScore to typeof(double), ExpectedUsage to typeof(long) | where abs(AnomalyScore) > 10 | project TimeGenerated,Computer, Namespace, ActualUsage,ExpectedUsage, abs(AnomalyScore) | sort by abs(AnomalyScore) desc"
    
    logger.info(f"GetAnomalies: Executing query with timespan: {timespan}")
    logger.info(f"GetAnomalies: Workspace ID: {workspace_id}")
    logger.info(f"GetAnomalies: Query: {query}")

    response = log_analytics_tool(self, query, workspace_id, timespan)
    if not response:
        logger.error("GetAnomalies: No response from Log Analytics Tool")
        return json.dumps({"error": "No response from Log Analytics Tool"})

    return response


agent_functions: Set[Callable[..., Any]] = {
    GetServerMetadata,
    GetSqlBpAssessment,
    GetSqlMetadata,
    GetPatchingLevel,
    GetAnomalies
}