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
