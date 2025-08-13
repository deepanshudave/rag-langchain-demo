#!/usr/bin/env python3

"""
Document Indexing Module for RAG System with Incremental Updates
Handles document loading, processing, and vector storage with file tracking
"""

from common.vector_store import VectorStore
from indexer.document_loader import DocumentLoader
from indexer.text_processor import TextProcessor
from indexer.file_tracker import FileTracker
from common.utils import (
    load_environment, validate_file_path, validate_directory_path,
    print_section_header, print_success, print_error, print_info, print_warning, confirm_action
)
from common.config import ERROR_MESSAGES, SUCCESS_MESSAGES
import os
import glob

class DocumentIndexer:
    def __init__(self, collection_name: str = None):
        load_environment()
        
        # Initialize components
        self.vector_store = VectorStore(collection_name=collection_name)
        self.document_loader = DocumentLoader()
        self.text_processor = TextProcessor()
        self.file_tracker = FileTracker()
        
        print("Document Indexer initialized successfully!")
    
    def index_documents_from_directory(self, documents_path: str = None, force_reindex: bool = False):
        """Load and index documents from a directory with incremental updates"""
        print_section_header("Starting Incremental Document Indexing")
        
        if not validate_directory_path(documents_path):
            return False
        
        documents_path = documents_path or self.document_loader.documents_path
        
        # Find all supported files
        file_patterns = ['*.pdf', '*.txt', '*.md']
        all_files = []
        for pattern in file_patterns:
            all_files.extend(glob.glob(os.path.join(documents_path, pattern)))
        
        if not all_files:
            print_error(ERROR_MESSAGES["no_documents"])
            return False
        
        print_info(f"Found {len(all_files)} files to process")
        
        # Check which files need indexing
        file_status = self.file_tracker.get_modified_files(all_files)
        
        new_files = [f for f, status in file_status.items() if status == 'new']
        modified_files = [f for f, status in file_status.items() if status == 'modified']
        unchanged_files = [f for f, status in file_status.items() if status == 'unchanged']
        
        print_info(f"📄 New files: {len(new_files)}")
        print_info(f"🔄 Modified files: {len(modified_files)}")
        print_info(f"✅ Unchanged files: {len(unchanged_files)}")
        
        if force_reindex:
            files_to_process = all_files
            print_info("🔄 Force reindex: processing all files")
        else:
            files_to_process = new_files + modified_files
            if unchanged_files:
                print_info(f"⏭️ Skipping {len(unchanged_files)} unchanged files")
        
        if not files_to_process:
            print_success("✅ All files are up to date, nothing to index!")
            return True
        
        # Process files that need indexing
        total_chunks = 0
        for file_path in files_to_process:
            success, chunk_count = self.index_single_file(file_path, update_tracking=False)
            if success:
                total_chunks += chunk_count
        
        # Update tracking for all processed files
        for file_path in files_to_process:
            if file_path in [f for f, _ in file_status.items()]:
                chunk_count = self.file_tracker.get_file_chunk_count(file_path)
                self.file_tracker.store_file_metadata(file_path, chunk_count)
        
        # Cleanup deleted files
        deleted_files = self.file_tracker.cleanup_deleted_files(all_files)
        if deleted_files:
            print_info(f"🗑️ Cleaned up {len(deleted_files)} deleted files")
        
        print_success(f"✅ Indexing complete! Processed {len(files_to_process)} files, {total_chunks} chunks")
        return True
    
    def index_single_file(self, file_path: str, update_tracking: bool = True) -> tuple[bool, int]:
        """Index a single file with incremental update support"""
        file_name = os.path.basename(file_path)
        
        if not validate_file_path(file_path):
            return False, 0
        
        # Check if file needs indexing
        is_modified, status = self.file_tracker.is_file_modified(file_path)
        
        if not is_modified and status == 'unchanged':
            chunk_count = self.file_tracker.get_file_chunk_count(file_path)
            print_info(f"⏭️ Skipping unchanged file: {file_name} ({chunk_count} chunks)")
            return True, chunk_count
        
        print_section_header(f"Indexing File: {file_name} [{status}]")
        
        # Generate file_id for tracking
        file_id = self.file_tracker.generate_file_id(file_path)
        
        # If file was modified, remove old chunks first
        if status == 'modified':
            removed_count = self.vector_store.remove_documents_by_file_id(file_id)
            print_info(f"🗑️ Removed {removed_count} old chunks")
        
        # Load documents
        try:
            if file_path.endswith('.pdf'):
                documents = self.document_loader.load_pdf(file_path)
            elif file_path.endswith(('.txt', '.md')):
                documents = self.document_loader.load_text(file_path)
            else:
                print_error(ERROR_MESSAGES["invalid_file_type"])
                return False, 0
        except Exception as e:
            print_error(f"Error loading file: {str(e)}")
            return False, 0
        
        if not documents:
            print_error("No content found in file")
            return False, 0
        
        # Process and index with file_id
        success, chunk_count = self._process_and_index_documents(documents, file_id)
        
        if success and update_tracking:
            # Update file tracking
            self.file_tracker.store_file_metadata(file_path, chunk_count)
            print_success(f"✅ Indexed {file_name}: {chunk_count} chunks")
        
        return success, chunk_count
    
    def _process_and_index_documents(self, documents, file_id: str = None) -> tuple[bool, int]:
        """Internal method to process and index documents with file tracking"""
        try:
            # Process and chunk documents
            chunked_docs = self.text_processor.chunk_documents(documents)
            
            # Extract text and metadata for vector store
            texts = self.text_processor.extract_text_from_chunks(chunked_docs)
            metadatas = self.text_processor.get_chunk_metadata(chunked_docs)
            
            # Add to vector store with file_id
            chunk_ids = self.vector_store.add_documents(
                documents=texts,
                metadatas=metadatas,
                file_id=file_id
            )
            
            chunk_count = len(texts)
            return True, chunk_count
            
        except Exception as e:
            print_error(f"Error during indexing: {str(e)}")
            return False, 0
    
    def get_index_status(self):
        """Get comprehensive information about the current index"""
        vector_info = self.vector_store.get_collection_info()
        print_section_header("Index Status")
        
        print(f"📚 Collection: {vector_info['name']}")
        print(f"📄 Total chunks: {vector_info['count']}")
        print(f"🗂️ Unique files: {vector_info.get('unique_files', 'Unknown')}")
        print(f"💾 Storage: {vector_info['persist_directory']}")
        
        # Show file tracking status
        print("")
        self.file_tracker.print_tracking_status()
        
        return vector_info
    
    def clear_index(self):
        """Clear all indexed documents and file tracking"""
        # Clear document collection
        self.vector_store.clear_collection()
        
        # Clear file metadata collection
        try:
            self.file_tracker.client.delete_collection(name="file_metadata")
            self.file_tracker.metadata_collection = self.file_tracker.client.create_collection(name="file_metadata")
            print_info("🗑️ Cleared file tracking data")
        except Exception as e:
            print_warning(f"Error clearing file tracking: {e}")
        
        print_success(SUCCESS_MESSAGES["index_cleared"])
        return True

def main():
    """Command line interface for indexing"""
    import sys
    
    indexer = DocumentIndexer()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python -m indexer.main directory [path]    - Index all files in directory")
        print("  python -m indexer.main file <path>         - Index single file")
        print("  python -m indexer.main status              - Show index status")
        print("  python -m indexer.main clear               - Clear index")
        print("  python -m indexer.main force [path]        - Force reindex all files")
        return
    
    command = sys.argv[1].lower()
    
    if command == "directory":
        path = sys.argv[2] if len(sys.argv) > 2 else None
        indexer.index_documents_from_directory(path)
    
    elif command == "file":
        if len(sys.argv) < 3:
            print("Error: File path required")
            return
        indexer.index_single_file(sys.argv[2])
    
    elif command == "force":
        path = sys.argv[2] if len(sys.argv) > 2 else None
        indexer.index_documents_from_directory(path, force_reindex=True)
    
    elif command == "status":
        indexer.get_index_status()
    
    elif command == "clear":
        if confirm_action("Are you sure you want to clear the index?"):
            indexer.clear_index()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()