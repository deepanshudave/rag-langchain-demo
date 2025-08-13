"""
Configuration settings for RAG Demo
Centralized configuration management for all hardcoded values
"""

# Model Configuration
MODEL_CONFIG = {
    "name": "claude-3-haiku-20240307",  # Current Claude model
    "temperature": 0.1,
    "max_tokens": 800,  # Reduced from 4000 for cost optimization
    "max_tokens_complex": 1200,  # For complex queries
    "fallback_model": "claude-3-haiku-20240307"  # Faster, cheaper fallback
}

# Text Processing Configuration
TEXT_CONFIG = {
    "chunk_size": 600,  # Reduced from 1000 for token optimization
    "chunk_overlap": 100,  # Reduced from 200
    "separators": ["\n\n", "\n", " ", ""],
    "min_chunk_size": 50,
    "max_chunk_size": 800  # Reduced from 2000
}

# Vector Store Configuration
VECTOR_CONFIG = {
    "collection_name": "documents",
    "persist_directory": "./chroma_db",
    "similarity_search_k": 3,  # Reduced from 5 for token optimization
    "similarity_search_k_complex": 5,  # For complex queries
    "max_results": 8,  # Reduced from 10
    "distance_threshold": 1.5
}

# Document Loading Configuration
DOCUMENT_CONFIG = {
    "documents_directory": "./source_documents",
    "supported_extensions": [".pdf", ".txt", ".md"],
    "max_file_size_mb": 50,
    "encoding": "utf-8"
}

# RAG Prompt Templates - Optimized for token efficiency
PROMPTS = {
    "system_prompt": """Answer using the provided context. Say "I don't know" if the context doesn't contain the answer. Be concise.""",
    
    "human_prompt": """Context:\n{context}\n\nQ: {question}""",
    
    "standalone_prompt": """Answer this question: {question}""",
    
    "context_format": "[{index}] {source}:\n{content}\n"
}

# API Configuration
API_CONFIG = {
    "anthropic_api_key_env": "ANTHROPIC_API_KEY",
    "request_timeout": 60,
    "max_retries": 3,
    "retry_delay": 1
}

# Application Configuration
APP_CONFIG = {
    "app_name": "RAG Demo",
    "version": "1.0.0",
    "debug_mode": False,
    "log_level": "INFO",
    "max_history": 100
}

# File Paths
PATHS = {
    "env_file": ".env",
    "env_example": ".env.example",
    "requirements": "requirements.txt",
    "readme": "README.md",
    "setup_script": "setup_env.sh"
}

# Validation Rules
VALIDATION = {
    "min_question_length": 3,
    "max_question_length": 1000,
    "min_document_length": 10,
    "required_env_vars": ["ANTHROPIC_API_KEY"]
}

# UI Configuration
UI_CONFIG = {
    "menu_options": [
        "Index documents from directory",
        "Ask a question", 
        "Show system status",
        "Clear index",
        "Exit"
    ],
    "welcome_message": "🚀 RAG System Demo",
    "goodbye_message": "Goodbye! 👋"
}

# Error Messages
ERROR_MESSAGES = {
    "api_key_missing": "❌ Anthropic API key not found! Please set ANTHROPIC_API_KEY in .env file",
    "no_documents": "No documents found to index!",
    "invalid_file_type": "Unsupported file type",
    "file_too_large": "File size exceeds maximum allowed size",
    "empty_query": "Please enter a valid question",
    "indexing_failed": "Failed to index documents",
    "query_failed": "Failed to process query"
}

# Success Messages  
SUCCESS_MESSAGES = {
    "documents_indexed": "✅ Successfully indexed {count} document chunks!",
    "text_indexed": "✅ Successfully indexed {count} text chunks!",
    "index_cleared": "✅ Cleared all indexed documents!",
    "setup_complete": "✅ Setup complete!"
}