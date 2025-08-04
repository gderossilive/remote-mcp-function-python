import json
import logging
import datetime
import azure
import azure.monitor.query
from azure.monitor.query import LogsQueryStatus
from utils.logging_decorators import log_method_call
from dateutil.relativedelta import relativedelta
from azure.identity import AzureCliCredential
from azure.core.exceptions import HttpResponseError
from azure.monitor.query import LogsQueryClient
from datetime import timedelta
import re
import time

logger = logging.getLogger(__name__)

class LogAnalyticsTool:
    """Tool for executing KQL queries on Azure Log Analytics."""
    
    def __init__(self):
        # Use AzureCliCredential which supports multiple authentication methods
        logger.info("Initializing LogAnalyticsTool")
        self.credential = AzureCliCredential()
        self.client = LogsQueryClient(self.credential)
        self.start_time = time.time()
    
    @log_method_call  # Applying logging decorator
    def _parse_timespan(self, timespan):
        """Parse timespan string into start and end datetime objects."""
        end_time = datetime.datetime.now()
        
        # Handle simple format like "30d", "1h", etc.
        if isinstance(timespan, str) and not timespan.startswith('P'):
            unit = timespan[-1].lower()
            try:
                value = int(timespan[:-1])
                if unit == 'd':
                    start_time = end_time - timedelta(days=value)
                elif unit == 'h':
                    start_time = end_time - timedelta(hours=value)
                elif unit == 'm':
                    start_time = end_time - timedelta(minutes=value)
                else:
                    # Default to days if unit is not recognized
                    start_time = end_time - timedelta(days=int(timespan))
            except ValueError:
                # Default to 1 day if parsing fails
                start_time = end_time - timedelta(days=1)
        # Handle ISO 8601 format if it's still used elsewhere
        elif isinstance(timespan, str) and timespan.startswith('P'):
            # ISO 8601 duration parsing logic
            match = re.match(r'P(\d+)D', timespan)
            if match:
                days = int(match.group(1))
                start_time = end_time - timedelta(days=days)
            else:
                # Default to 1 day
                start_time = end_time - timedelta(days=1)
        else:
            # Handle any other format or default
            start_time = end_time - timedelta(days=1)
        
        logging.info(f"Parsed timespan: ({start_time}, {end_time})")
        return start_time, end_time
    
    @log_method_call
    def run_query(self, query, workspace_id, timespan=None):
        logger.info("Entering method: LogAnalyticsTool.run_query")
        start_time = time.time()
        
        try:
            # Verify workspace ID format
            if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', workspace_id, re.I):
                logger.warning(f"Workspace ID format appears invalid: {workspace_id}")
                
            # Diagnostic info
            logger.info(f"Attempting to query workspace: {workspace_id}")
            logger.info(f"Using credential type: {type(self.credential).__name__}")
            
            parsed_timespan = self._parse_timespan(timespan)

            logger.info(f"Parsed timespan: {parsed_timespan}")
            
            response = self.client.query_workspace(
                workspace_id=workspace_id,
                query=query,
                timespan=parsed_timespan
            )

            import pandas as pd
            tables = []
            for table in response.tables:
                df = pd.DataFrame(data=table.rows, columns=table.columns)
                tables.append(df)
            return tables
            """            
            if response.status == LogsQueryStatus.SUCCESS:
                tables = []
                for table in response.tables:
                    # Convert each row to a serializable dictionary
                    rows = []
                    for row in table.rows:
                        # Convert LogsTableRow to dictionary
                        row_dict = {}
                        for i, col in enumerate(table.columns):
                            col_name = col.name if hasattr(col, 'name') else f"column{i}"
                            row_dict[col_name] = row[i]
                        rows.append(row_dict)
                    
                    # Create serializable table structure
                    table_dict = {
                        "name": table.name if hasattr(table, 'name') else "results",
                        "columns": [col.name if hasattr(col, 'name') else str(col) for col in table.columns],
                        "rows": rows
                    }
                    tables.append(table_dict)
                
                return {
                    "tables": tables,
                    "total_rows": sum(len(table["rows"]) for table in tables)
                }
            else:
                logger.error(f"Query failed with status: {response.status}")
                return {"error": f"Query failed with status: {response.status}"}
            """
                
        except azure.core.exceptions.ResourceNotFoundError as e:
            logger.error(f"Workspace not found or inaccessible: {workspace_id}")
            logger.error(f"An unexpected error occurred: {str(e)}")
            logger.error(f"Exception details:", exc_info=True)
            return {"error": str(e)}
        except Exception as e:
            logger.error(f"An unexpected error occurred: {str(e)}")
            logger.error(f"Exception details:", exc_info=True)
            return {"error": str(e)}
        finally:
            execution_time = time.time() - start_time
            logger.info(f"Exiting method: LogAnalyticsTool.run_query - Execution time: {execution_time:.4f}s")