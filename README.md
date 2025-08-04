<!--
---
name: Remote MCP with Azure Functions (Python)
description: Run a remote MCP server on Azure functions.  
page_type: sample
languages:
- python
- bicep
- azdeveloper
products:
- azure-functions
- azure
urlFragment: remote-mcp-functions-python
---
-->

# Getting Started with Remote MCP Servers using Azure Functions (Python)

This is a quickstart template to easily build and deploy a custom remote MCP server to the cloud using Azure Functions with Python. You can clone/restore/run on your local machine with debugging, and `azd up` to have it in the cloud in a couple minutes. The MCP server is secured by design using keys and HTTPS, and allows more options for OAuth using built-in auth and/or [API Management](https://aka.ms/mcp-remote-apim-auth) as well as network isolation using VNET.

**Updated August 4, 2025**: This template now includes advanced Azure infrastructure analysis tools with integrated MCP agent functions for server monitoring, SQL analysis, patch management, best practices assessment, and anomaly detection.

If you're looking for this sample in more languages check out the [.NET/C#](https://github.com/Azure-Samples/remote-mcp-functions-dotnet) and [Node.js/TypeScript](https://github.com/Azure-Samples/remote-mcp-functions-typescript) versions.

[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/Azure-Samples/remote-mcp-functions-python)

Below is the architecture diagram for the Remote MCP Server using Azure Functions:

![Architecture Diagram](architecture-diagram.png)

## Prerequisites

+ [Python](https://www.python.org/downloads/) version 3.11 or higher
+ [Azure Functions Core Tools](https://learn.microsoft.com/azure/azure-functions/functions-run-local?pivots=programming-language-python#install-the-azure-functions-core-tools) >= `4.0.7030`
+ [Azure Developer CLI](https://aka.ms/azd)
+ To use Visual Studio Code to run and debug locally:
  + [Visual Studio Code](https://code.visualstudio.com/)
  + [Azure Functions extension](https://marketplace.visualstudio.com/items?itemName=ms-azuretools.vscode-azurefunctions)

## Available MCP Tools

This template includes several powerful MCP tools for Azure infrastructure analysis:

### Basic Tools
- **hello_mcp** - Simple greeting function for testing connectivity
- **get_snippet** - Retrieve code snippets stored in Azure Blob Storage
- **save_snippet** - Save code snippets to Azure Blob Storage

### Azure Infrastructure Analysis Tools (New!)
- **GetServerMetadata** - Retrieve comprehensive server infrastructure configuration including OS version, CPU details, memory, and network information
- **GetSqlMetadata** - Analyze SQL Server infrastructure including database configurations, licensing, storage usage, and backup information
- **GetPatchingLevel** - Identify missing patches and security updates across your server infrastructure with detailed metadata
- **GetSqlBpAssessment** - Run SQL Server best practices assessment to identify configuration issues and improvement opportunities
- **GetAnomalies** - Detect performance anomalies in server metrics using AI-powered analysis of CPU and disk usage patterns

These tools leverage Azure Resource Graph for infrastructure queries and Azure Monitor/Log Analytics for performance data analysis.

## Prepare your local environment

For local development, the function app uses managed identity authentication with Azure Storage to avoid key-based authentication. The infrastructure analysis tools require Azure CLI authentication to access Azure Resource Graph and Monitor APIs.

1. Ensure you're logged in to Azure CLI:

    ```shell
    az login
    ```

2. **Optional**: Start Azurite for local blob storage testing (if you want to test snippet functionality locally):

    ```shell
    docker run -p 10000:10000 -p 10001:10001 -p 10002:10002 \
        mcr.microsoft.com/azure-storage/azurite
    ```

>**Note**: The infrastructure analysis tools work with live Azure resources and require proper Azure authentication and permissions. Local storage emulation is only needed for the snippet save/retrieve functionality.

## Run your MCP Server locally from the terminal

1. Change to the src folder in a new terminal window:

   ```shell
   cd src
   ```

1. Install Python dependencies:

   ```shell
   pip install -r requirements.txt
   ```

   The following Azure SDK packages are included for the infrastructure analysis tools:
   - `azure-identity` - For Azure authentication
   - `azure-mgmt-resourcegraph` - For querying Azure Resource Graph
   - `azure-monitor-query` - For Log Analytics queries
   - `pandas` - For data processing
   - `python-dateutil` - For date/time handling

>**Note** it is a best practice to create a Virtual Environment before doing the `pip install` to avoid dependency issues/collisions, or if you are running in CodeSpaces.  See [Python Environments in VS Code](https://code.visualstudio.com/docs/python/environments#_creating-environments) for more information.

1. Start the Functions host locally:

   ```shell
   func start
   ```

> **Note** by default this will use the webhooks route: `/runtime/webhooks/mcp/sse`.  Later we will use this in Azure to set the key on client/host calls: `/runtime/webhooks/mcp/sse?code=<system_key>`

## Connect to the *local* MCP server from a client/host

### VS Code - Copilot agent mode

1. **Add MCP Server** from command palette and add URL to your running Function app's SSE endpoint:

    ```shell
    http://0.0.0.0:7071/runtime/webhooks/mcp/sse
    ```

1. **List MCP Servers** from command palette and start the server
1. In Copilot chat agent mode enter a prompt to trigger the tool, e.g., select some code and enter this prompt

    ```plaintext
    Say Hello
    ```

    ```plaintext
    Save this snippet as snippet1 
    ```

    ```plaintext
    Retrieve snippet1 and apply to newFile.py
    ```

    **Try the new Azure infrastructure analysis tools:**

    ```plaintext
    Get server metadata for subscription 06dbbc7b-2363-4dd4-9803-95d07f1a8d3e
    ```

    ```plaintext
    Analyze SQL infrastructure configuration for my Azure environment
    ```

    ```plaintext
    Check for missing patches on all servers
    ```

    ```plaintext
    Run SQL best practices assessment on workspace 93819b8e-f60e-40cf-8b96-9c9113b2b97e
    ```

    ```plaintext
    Detect performance anomalies in the last 7 days
    ```

1. When prompted to run the tool, consent by clicking **Continue**

1. When you're done, press Ctrl+C in the terminal window to stop the Functions host process.

### MCP Inspector

1. In a **new terminal window**, install and run MCP Inspector

    ```shell
    npx @modelcontextprotocol/inspector
    ```

2. CTRL click to load the MCP Inspector web app from the URL displayed by the app (e.g. http://0.0.0.0:5173/#resources)
3. Set the transport type to `SSE`
4. Set the URL to your running Function app's SSE endpoint and **Connect**:

    ```shell
    http://0.0.0.0:7071/runtime/webhooks/mcp/sse
    ```

>**Note** this step will not work in CodeSpaces.  Please move on to Deploy to Remote MCP.  

5. **List Tools**.  Click on a tool and **Run Tool**.

## Verify local blob storage in Azurite

After testing the snippet save functionality locally, you can verify that blobs are being stored correctly in your local Azurite storage emulator.

### Using Azure Storage Explorer

1. Open Azure Storage Explorer
1. In the left panel, expand **Emulator & Attached** → **Storage Accounts** → **(Emulator - Default Ports) (Key)**
1. Navigate to **Blob Containers** → **snippets**
1. You should see any saved snippets as blob files in this container
1. Double-click on any blob to view its contents and verify the snippet data was saved correctly

### Using Azure CLI (Alternative)

If you prefer using the command line, you can also verify blobs using Azure CLI with the storage emulator:

```shell
# List blobs in the snippets container
az storage blob list --container-name snippets --connection-string "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
```

```shell
# Download a specific blob to view its contents
az storage blob download --container-name snippets --name <blob-name> --file <local-file-path> --connection-string "DefaultEndpointsProtocol=http;AccountName=devstoreaccount1;AccountKey=Eby8vdM02xNOcqFlqUwJPLlmEtlCDXJ1OUzFT50uSRZ6IFsuFq2UVErCz4I6tq/K1SZFPTOtr/KBHBeksoGMGw==;BlobEndpoint=http://127.0.0.1:10000/devstoreaccount1;"
```

This verification step ensures your MCP server is correctly interacting with the local storage emulator and that the blob storage functionality is working as expected before deploying to Azure.

## Deploy to Azure for Remote MCP

Run this [azd](https://aka.ms/azd) command to provision the function app, with any required Azure resources, and deploy your code:

```shell
azd up
```

**Recent Updates (August 4, 2025):**
- Storage configuration updated to use LRS (Locally Redundant Storage) for broader region availability
- Managed identity authentication enabled for enhanced security
- Key-based storage authentication disabled as per security best practices
- Added comprehensive Azure SDK dependencies for infrastructure analysis

You can opt-in to a VNet being used in the sample. To do so, do this before `azd up`

```bash
azd env set VNET_ENABLED true
```

Additionally, [API Management]() can be used for improved security and policies over your MCP Server, and [App Service built-in authentication](https://learn.microsoft.com/azure/app-service/overview-authentication-authorization) can be used to set up your favorite OAuth provider including Entra.  

## Connect to your *remote* MCP server function app from a client

Your client will need a key in order to invoke the new hosted SSE endpoint, which will be of the form `https://<funcappname>.azurewebsites.net/runtime/webhooks/mcp/sse`. The hosted function requires a system key by default which can be obtained from the [portal](https://learn.microsoft.com/azure/azure-functions/function-keys-how-to?tabs=azure-portal) or the CLI (`az functionapp keys list --resource-group <resource_group> --name <function_app_name>`). Obtain the system key named `mcp_extension`.

### Connect to remote MCP server in MCP Inspector
For MCP Inspector, you can include the key in the URL: 
```plaintext
https://<funcappname>.azurewebsites.net/runtime/webhooks/mcp/sse?code=<your-mcp-extension-system-key>
```

### Connect to remote MCP server in VS Code - GitHub Copilot
For GitHub Copilot within VS Code, you should instead set the key as the `x-functions-key` header in `mcp.json`, and you would just use `https://<funcappname>.azurewebsites.net/runtime/webhooks/mcp/sse` for the URL. The following example uses an input and will prompt you to provide the key when you start the server from VS Code.  Note [mcp.json](.vscode/mcp.json) has already been included in this repo and will be picked up by VS Code.  Click Start on the server to be prompted for values including `functionapp-name` (in your /.azure/*/.env file) and `functions-mcp-extension-system-key` which can be obtained from CLI command above or API Keys in the portal for the Function App.  

```json
{
    "inputs": [
        {
            "type": "promptString",
            "id": "functions-mcp-extension-system-key",
            "description": "Azure Functions MCP Extension System Key",
            "password": true
        },
        {
            "type": "promptString",
            "id": "functionapp-name",
            "description": "Azure Functions App Name"
        }
    ],
    "servers": {
        "remote-mcp-function": {
            "type": "sse",
            "url": "https://${input:functionapp-name}.azurewebsites.net/runtime/webhooks/mcp/sse",
            "headers": {
                "x-functions-key": "${input:functions-mcp-extension-system-key}"
            }
        },
        "local-mcp-function": {
            "type": "sse",
            "url": "http://0.0.0.0:7071/runtime/webhooks/mcp/sse"
        }
    }
}
```

For MCP Inspector, you can include the key in the URL: `https://<funcappname>.azurewebsites.net/runtime/webhooks/mcp/sse?code=<your-mcp-extension-system-key>`.

For GitHub Copilot within VS Code, you should instead set the key as the `x-functions-key` header in `mcp.json`, and you would just use `https://<funcappname>.azurewebsites.net/runtime/webhooks/mcp/sse` for the URL. The following example uses an input and will prompt you to provide the key when you start the server from VS Code:

```json
{
    "inputs": [
        {
            "type": "promptString",
            "id": "functions-mcp-extension-system-key",
            "description": "Azure Functions MCP Extension System Key",
            "password": true
        }
    ],
    "servers": {
        "my-mcp-server": {
            "type": "sse",
            "url": "<funcappname>.azurewebsites.net/runtime/webhooks/mcp/sse",
            "headers": {
                "x-functions-key": "${input:functions-mcp-extension-system-key}"
            }
        }
    }
}
```

## Redeploy your code

You can run the `azd up` command as many times as you need to both provision your Azure resources and deploy code updates to your function app.

>[!NOTE]
>Deployed code files are always overwritten by the latest deployment package.

## Clean up resources

When you're done working with your function app and related resources, you can use this command to delete the function app and its related resources from Azure and avoid incurring any further costs:

```shell
azd down
```

## Helpful Azure Commands

Once your application is deployed, you can use these commands to manage and monitor your application:

```bash
# Get your function app name from the environment file
FUNCTION_APP_NAME=$(cat .azure/$(cat .azure/config.json | jq -r '.defaultEnvironment')/env.json | jq -r '.FUNCTION_APP_NAME')
echo $FUNCTION_APP_NAME

# Get resource group 
RESOURCE_GROUP=$(cat .azure/$(cat .azure/config.json | jq -r '.defaultEnvironment')/env.json | jq -r '.AZURE_RESOURCE_GROUP')
echo $RESOURCE_GROUP

# View function app logs
az webapp log tail --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP

# Redeploy the application without provisioning new resources
azd deploy
```

## Source Code

The function code for the MCP tools is defined in the Python files in the `src` directory. The MCP function annotations expose these functions as MCP Server tools.

### Core Files
- **`function_app.py`** - Main Azure Function app with MCP tool definitions
- **`agent_functions.py`** - Azure infrastructure analysis functions
- **`utils/`** - Utility classes for Azure Resource Graph and Log Analytics integration
  - `resource_graph_tool.py` - Azure Resource Graph query execution
  - `log_analytics_tool.py` - Log Analytics/Azure Monitor queries
  - `logging_decorators.py` - Logging and debugging utilities

### Example Tool Implementation

Here's an example of how the infrastructure analysis tools are implemented:

### Example Tool Implementation

Here's an example of how the infrastructure analysis tools are implemented:

```python
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
```

**Basic snippet management tools:**

```python
@app.generic_trigger(arg_name="context", type="mcpToolTrigger", toolName="hello_mcp", 
                     description="Hello world.", 
                     toolProperties="[]")
def hello_mcp(context) -> None:
    """
    A simple function that returns a greeting message.
    """
    return "Hello I am MCPTool!"


@app.generic_trigger(
    arg_name="context",
    type="mcpToolTrigger",
    toolName="get_snippet",
    description="Retrieve a snippet by name.",
    toolProperties=tool_properties_get_snippets_json
)
@app.generic_input_binding(
    arg_name="file",
    type="blob",
    connection="AzureWebJobsStorage",
    path=_BLOB_PATH
)
def get_snippet(file: func.InputStream, context) -> str:
    """
    Retrieves a snippet by name from Azure Blob Storage.
    """
    snippet_content = file.read().decode("utf-8")
    logging.info(f"Retrieved snippet: {snippet_content}")
    return snippet_content
```

Note that the `host.json` file also includes a reference to the experimental bundle, which is required for apps using this feature:

```json
"extensionBundle": {
  "id": "Microsoft.Azure.Functions.ExtensionBundle.Experimental",
  "version": "[4.*, 5.0.0)"
}
```

## Next Steps

- Add [API Management](https://aka.ms/mcp-remote-apim-auth) to your MCP server (auth, gateway, policies, more!)
- Add [built-in auth](https://learn.microsoft.com/en-us/azure/app-service/overview-authentication-authorization) to your MCP server
- Enable VNET using VNET_ENABLED=true flag
- Learn more about [related MCP efforts from Microsoft](https://github.com/microsoft/mcp/tree/main/Resources)

## Changelog

### August 4, 2025
- **Added Azure Infrastructure Analysis Tools**: Integrated 5 new MCP tools for comprehensive Azure infrastructure monitoring and analysis
- **Enhanced Security**: Implemented managed identity authentication and disabled key-based storage access
- **Storage Optimization**: Updated storage configuration to use LRS for broader regional availability
- **Dependencies Update**: Added Azure SDK packages for Resource Graph and Monitor APIs
- **Improved Documentation**: Updated README with comprehensive tool descriptions and usage examples

### Tool Details Added:
- **GetServerMetadata**: Server infrastructure analysis (OS, CPU, memory, network)
- **GetSqlMetadata**: SQL Server configuration and database analysis
- **GetPatchingLevel**: Security patch analysis and missing update identification
- **GetSqlBpAssessment**: SQL Server best practices assessment via Log Analytics
- **GetAnomalies**: AI-powered performance anomaly detection for server metrics
