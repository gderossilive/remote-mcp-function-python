#!/bin/bash
echo "Deploying to Azure..."
cd /workspaces/python-2
azd deploy
echo "Deployment completed."
