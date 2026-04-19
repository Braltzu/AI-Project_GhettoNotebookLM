Azure AI RAG Document Processor

A Python-based RAG (Retrieval-Augmented Generation) pipeline that automates document classification, Azure Blob Storage uploads, and intelligent querying using Azure AI Search and Azure OpenAI.
 Overview

This project provides an end-to-end workflow for managing documents in the cloud and interacting with them via AI. It consists of two main phases:

    Ingestion & Classification: Automatically identifies the topic of local PDF files using LLMs, then uploads them to Azure Blob Storage for indexing.

    Intelligent Querying: A LangGraph-powered state machine that retrieves context from Azure AI Search and generates grounded answers using Azure OpenAI.

 Features

    Automated Topic Identification: Uses Azure OpenAI to scan document headers and categorize files before processing.

    Managed RAG: Leverages AzureAISearchRetriever for server-side vector search and semantic ranking.

    Stateful Workflow: Built with LangGraph to manage the flow between retrieval and response generation.

    PDF Report Generation: Automatically saves AI-generated answers into formatted PDF documents in a Processed_Files directory.

    Azure Integration: Native support for Azure AI Foundry (formerly Azure AI Studio) components.

 Tech Stack

    Orchestration: LangGraph, LangChain

    AI Services: Azure OpenAI (GPT-4o/3.5), Azure AI Search

    Storage: Azure Blob Storage

    PDF Handling: pypdf, fpdf

 Prerequisites

Before running the script, ensure you have:

    An active Azure Subscription.

    An Azure AI Search index created and populated.

    An Azure Storage Account with a container.

    A deployment of an LLM in Azure OpenAI / AI Foundry.

Environment Variables

Create a .env file in the root directory with the following keys:
Koodinpätkä

# Azure Storage
AZURE_STORAGE_CONNECTION_STR="your_connection_string"
CONTAINER_NAME="your_container_name"

# Azure AI Search
AZURE_SEARCH_SERVICE_NAME="your_service_name"
AZURE_SEARCH_INDEX_NAME="your_index_name"
AZURE_SEARCH_API_KEY="your_api_key"
AZURE_SEARCH_CONTENT_FIELD="content"
AZURE_SEARCH_TOP_K=3

# Azure OpenAI
AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/"
AZURE_OPENAI_API_KEY="your_api_key"
AZURE_OPENAI_DEPLOYMENT="your_deployment_name"
AZURE_OPENAI_API_VERSION="2024-12-01-preview"

 Setup & Usage

    Install Dependencies:

    pip install -r requirements.txt

    Prepare Files:
    Place the PDF documents you want to process into a folder named FILES_TO_Process.

    Run the Pipeline:
    Bash

    python main.py

How it works:

    Phase 1: The script scans FILES_TO_Process, identifies topics, and uploads files to Azure.

    Phase 2: Enter a loop where you can ask questions about your documents.

    Phase 3: For every question asked, a summary PDF is generated in the Processed_Files folder.

 Logic Flow

The Querying engine follows a strict linear graph:

    START ➔ retrieve: Fetches relevant chunks from the Azure AI Search Index.

    retrieve ➔ generate: Feeds the chunks into the LLM with a system prompt to prevent hallucinations.

    generate ➔ END: Returns the answer and triggers the PDF export.

 Project Structure

    main.py - The core script containing logic for uploading, querying, and the StateGraph.

    FILES_TO_Process/ - Local source folder for input documents.

    Processed_Files/ - Output folder for generated AI response PDFs.

    .env - Configuration file (ignored by git).

 License

MIT License

AI-tools were used to help building the backend and learning Streamlit for the frontend UI, which we decided not to use in this project.

AI-tools used:

    Claude
    Google Gemini

What doesn't work, what's hardcoded, what would need to change for production?

    Source folder is currently hardcoded to a local folder and in production, this would likely be an automated trigger         from a SharePoint site, an email attachment, or a cloud upload UI.

    There's no error handling in the Graph and if the retriever fails, the whole graph crashes.
    The code imports PfdReader, but the main upload function just sends the raw file and doesn't read or clean the PDF          content before uploading. This means that in case the PDF is a scanned image, the search won't be able to read it           without an OCR step.

    Changes needed for production include:

    Asynchronous processing: Using async/await for the Azure calls so the app doesn't freeze while waiting for a large          PDF to upload.

    Vectorization Pipeline: An indexing splitter that breaks the documents into smaller, overlapping "chunks" so the            retriever can find the exact paragraph needed.

    Evaluation: A way to measure how "right" the answers are. We would need an evaluation layer to track if the AI is           actually using the context correctly over time.

       


