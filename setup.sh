#!/bin/bash

echo "Setting up RAG Demo..."

# Create and activate virtual environment
python3 -m venv rag-env
source rag-env/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file
cp .env.example .env
echo "Update .env file and add your ANTHROPIC_API_KEY"

###################
# Indexer Command #
###################
# python -m indexer.main directory source_documents/
# python -m indexer.main file source_documents/sample_document.txt
# python -m indexer.main status
# python -m indexer.main clear
# python -m indexer.main force source_documents/


###################
# Search Command  #
###################
# python -m search.main ask "What is machine learning?"
# python -m search.main ask "What is price of CHLORINATOR"
