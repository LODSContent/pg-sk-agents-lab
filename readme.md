## Overview

This lab guides you through developing an agent-driven, Retrieval-Augmented Generation (RAG) application that explores U.S. Case Law data. You'll learn how to combine PostgreSQL's powerful database capabilities with AI techniques to create a legal research assistant capable of providing accurate and contextually relevant answers.

## Architecture

![Architecture](./Docs/images/arch.png)

## Overview

## What You'll Build

- A Semantic Kernel Agent that can reason over legal cases stored in PostgreSQL
- A system that utilizes vector embeddings for semantic search
- Plugins for database search and external data retrieval 
- An application enhanced with the GraphRAG pattern for improved answer quality

## Key Technologies

- **Azure Database for PostgreSQL**: Database platform with AI extensions
- **Semantic Kernel**: Framework for building AI agents with plugins
- **Azure OpenAI**: For embeddings and LLM chat completions
- **PostgreSQL Extensions**: Vector and Graph capabilities (DiskANN, AGE)
- **Python**: For agent development and database interaction

## Project Structure

```
├── LICENSE                     # MIT License file
├── Code/
│   └── lab.ipynb              # Main Jupyter notebook tutorial
├── Dataset/
│   └── cases.csv              # Legal case dataset
├── Docs/
│   └── lab_manual.md          # Detailed lab instructions
├── Scripts/
│   ├── create_graph.sql       # SQL script for graph creation
│   ├── get_env.ps1            # Script to get environment variables
│   ├── initialize_dataset.sql # Database initialization script
│   ├── load_age.ps1           # Apache AGE installation script
│   └── setup_reranker.sql     # Configuration for semantic reranker
└── Setup/
    └── Infra/                 # Infrastructure setup files
        ├── deploy.bicep       # Azure Bicep deployment template
        └── deployment_script.ps1 # Deployment script
```

## Prerequisites

- Azure subscription with access to Azure OpenAI
- Visual Studio Code with the PostgreSQL extension
- Python environment with necessary libraries:
  - PostgreSQL connectivity (`psycopg`, `psycopg-binary`, `psycopg-pool`)
  - Modeling and validation (`pydantic`)
  - OpenAI and Semantic Kernel integration (`openai`, `semantic-kernel`)
  - Notebook compatibility (`nest_asyncio`, `ipykernel`)

## Lab Sections

1. **Setup Azure PostgreSQL Database**:
   - Database connection and configuration
   - Install the `azure_ai` extension
   - Configure Azure OpenAI connectivity

2. **Using AI-driven features in PostgreSQL**:
   - Pattern matching queries
   - Semantic vector search using embeddings
   - DiskANN indexing for fast vector similarity search

3. **Building the Agent Application**:
   - Setting up Semantic Kernel
   - Creating database search plugins
   - Implementing semantic reranking
   - Adding external data sources (weather API)
   - Testing and improving the agent

## Deploying to Azure

1. Set environment variables for resource group:

   ```bash
   export AZURE_RESOURCE_GROUP=<your-resource-group>
   export AZURE_LOCATION=<your-location>
   ```

2. Create a resource group:

   ```bash
   az group create --name $AZURE_RESOURCE_GROUP --location $AZURE_LOCATION
   ```

3. Deploy the infrastructure using Bicep:

   ```bash
   az deployment group create --resource-group $AZURE_RESOURCE_GROUP --template-file Setup/Infra/deploy.bicep --parameters restore=false --only-show-errors
   ```

4. Set up the PostgreSQL database and extensions:

   ```bash
   $aadUserPrincipalName = "@lab.CloudPortalCredential(User1).Username"
   $objectId = az ad user show --id $aadUserPrincipalName --query id --output tsv
   $resourceGroupName = "@lab.CloudResourceGroup(ResourceGroup1).Name"
   $server = az postgres flexible-server list --resource-group $resourceGroupName --query "[0].name" --output tsv

   az postgres flexible-server ad-admin create --resource-group $resourceGroupName --server-name $server --display-name $aadUserPrincipalName --object-id $objectId
   ```

## Getting Started

1. Follow the instructions in lab_manual.md to setup your environment
2. Open lab.ipynb in Visual Studio Code to follow the step-by-step guide

## Additional Resources

- [GraphRAG Solution for Azure Database for PostgreSQL](https://aka.ms/pg-graphrag)
- [Graph data in Azure Database for PostgreSQL](https://aka.ms/age-blog)
- [PostgreSQL extension for Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=ms-ossdata.vscode-postgresql)
- [Semantic Ranker Solution Accelerator](https://aka.ms/semantic-ranker-solution-accelerator-pg-blog)
- [Build your own advanced AI Copilot with Postgres](http://aka.ms/pg-byoac-docs)

## License

This project is licensed under the MIT License - see the LICENSE file for details.