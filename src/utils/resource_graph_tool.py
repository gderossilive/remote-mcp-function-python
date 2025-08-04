import json
import logging
from utils.logging_decorators import log_method_call
from azure.identity import AzureCliCredential
from azure.core.exceptions import HttpResponseError
from azure.mgmt.resourcegraph import ResourceGraphClient
from azure.mgmt.resourcegraph.models import QueryRequest, QueryRequestOptions

logger = logging.getLogger(__name__)

class ResourceGraphTool:
    """Tool for executing KQL queries on Azure Resource Graph."""
    
    def __init__(self):
        # Use DefaultAzureCredential which supports multiple authentication methods
        logger.info("Initializing ResourceGraphTool")
        self.credential = AzureCliCredential()
        self.client = ResourceGraphClient(self.credential)

    @log_method_call
    def run_query(self, query, subscription_ids=None):
        """
        Run a KQL query on Azure Resource Graph.
        
        Args:
            query (str): The KQL query to execute
            subscription_ids (list): List of subscription IDs to query against (optional)
            
        Returns:
            dict: Results of the query
        """
        try:
            # If subscription_ids is not provided, the query will run against all accessible subscriptions
            logger.debug(f"Running Resource Graph query: {query}")
            if subscription_ids:
                logger.debug(f"Using subscription IDs: {subscription_ids}")
            else:
                logger.debug("No subscription IDs provided, querying all accessible subscriptions")
                
            options = QueryRequestOptions(result_format="objectArray")
            request = QueryRequest(
                query=query,
                subscriptions=subscription_ids,
                options=options
            )
            
            logger.debug("Sending request to Resource Graph API")
            response = self.client.resources(request)
            
            # Convert response to a more easily consumable format
            result = {
                "data": response.data,
                "count": response.count,
                "total_records": response.total_records,
                "skip_token": response.skip_token
            }
            
            logger.debug(f"Query returned {response.count} results out of {response.total_records} total records")
            return result
        
        except HttpResponseError as e:
            error_msg = f"Query failed: {str(e)}"
            logger.error(error_msg)
            logger.exception("Exception details:")
            return {"error": error_msg}
        except Exception as e:
            error_msg = f"An unexpected error occurred: {str(e)}"
            logger.error(error_msg)
            logger.exception("Exception details:")
            return {"error": error_msg}