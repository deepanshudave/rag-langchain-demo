"""
Utility functions for RAG system
Common functions used by indexer and searcher modules
"""

import os
from dotenv import load_dotenv
from common.config import API_CONFIG, ERROR_MESSAGES, VALIDATION

def load_environment():
    """Load environment variables"""
    load_dotenv()

def check_api_key():
    """Check if Anthropic API key is set"""
    api_key = os.getenv(API_CONFIG["anthropic_api_key_env"])
    if not api_key:
        print(ERROR_MESSAGES["api_key_missing"])
        return False
    return True

def validate_query(query: str) -> bool:
    """Validate user query"""
    if not query or not query.strip():
        print("Empty query provided!")
        return False
    
    if len(query) < VALIDATION["min_question_length"]:
        print(f"Query too short! Minimum {VALIDATION['min_question_length']} characters required.")
        return False
    
    if len(query) > VALIDATION["max_question_length"]:
        print(f"Query too long! Maximum {VALIDATION['max_question_length']} characters allowed.")
        return False
    
    return True

def validate_file_path(file_path: str) -> bool:
    """Validate file path and type"""
    if not file_path:
        print("No file path provided!")
        return False
    
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return False
    
    if not os.path.isfile(file_path):
        print(f"Path is not a file: {file_path}")
        return False
    
    # Check file extension
    allowed_extensions = ['.pdf', '.txt', '.md']
    file_ext = os.path.splitext(file_path)[1].lower()
    
    if file_ext not in allowed_extensions:
        print(f"Unsupported file type: {file_ext}")
        print(f"Supported types: {', '.join(allowed_extensions)}")
        return False
    
    return True

def validate_directory_path(dir_path: str) -> bool:
    """Validate directory path"""
    if not dir_path:
        return True  # None/empty means use default
    
    if not os.path.exists(dir_path):
        print(f"Directory not found: {dir_path}")
        return False
    
    if not os.path.isdir(dir_path):
        print(f"Path is not a directory: {dir_path}")
        return False
    
    return True

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB"]
    i = 0
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f} {size_names[i]}"

def get_file_info(file_path: str) -> dict:
    """Get file information"""
    if not os.path.exists(file_path):
        return {}
    
    stat = os.stat(file_path)
    return {
        'name': os.path.basename(file_path),
        'path': file_path,
        'size': stat.st_size,
        'size_formatted': format_file_size(stat.st_size),
        'extension': os.path.splitext(file_path)[1].lower(),
        'is_file': os.path.isfile(file_path),
        'is_dir': os.path.isdir(file_path)
    }

def print_separator(char: str = "=", length: int = 50):
    """Print a separator line"""
    print(char * length)

def print_section_header(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*3} {title} {'='*3}")

def print_success(message: str):
    """Print success message with formatting"""
    print(f"✅ {message}")

def print_error(message: str):
    """Print error message with formatting"""
    print(f"❌ {message}")

def print_warning(message: str):
    """Print warning message with formatting"""
    print(f"⚠️ {message}")

def print_info(message: str):
    """Print info message with formatting"""
    print(f"ℹ️ {message}")

def confirm_action(message: str, default: bool = False) -> bool:
    """Ask user for confirmation"""
    suffix = " (y/N): " if not default else " (Y/n): "
    response = input(message + suffix).strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'true', '1']

def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix

def sanitize_filename(filename: str) -> str:
    """Sanitize filename by removing invalid characters"""
    import re
    # Remove invalid characters for filenames
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove multiple underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores and spaces
    sanitized = sanitized.strip('_ ')
    
    return sanitized if sanitized else 'untitled'