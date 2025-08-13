"""
File Tracking System using ChromaDB
Hybrid approach: File metadata in separate collection, file_id references in document chunks
"""

import os
import hashlib
import time
from typing import Dict, List, Optional, Tuple
import chromadb
from common.utils import print_info, print_success, print_warning, print_error
from common.config import VECTOR_CONFIG

class FileTracker:
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or VECTOR_CONFIG["persist_directory"]
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create file metadata collection
        try:
            self.metadata_collection = self.client.get_collection(name="file_metadata")
        except ValueError:
            self.metadata_collection = self.client.create_collection(name="file_metadata")
            print_info("Created file metadata collection")
    
    def generate_file_id(self, file_path: str) -> str:
        """Generate unique file ID from file path"""
        abs_path = os.path.abspath(file_path)
        return hashlib.md5(abs_path.encode()).hexdigest()
    
    def get_file_hash(self, file_path: str) -> str:
        """Calculate file content hash"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except IOError:
            return ""
    
    def get_file_metadata(self, file_path: str, include_hash: bool = True) -> Dict:
        """Get comprehensive file metadata"""
        if not os.path.exists(file_path):
            return {}
        
        stat = os.stat(file_path)
        abs_path = os.path.abspath(file_path)
        
        metadata = {
            'file_id': self.generate_file_id(file_path),
            'file_path': abs_path,
            'file_name': os.path.basename(file_path),
            'size': stat.st_size,
            'mtime': stat.st_mtime,
            'extension': os.path.splitext(file_path)[1].lower(),
            'indexed_at': time.time()
        }
        
        # Only calculate hash when needed (expensive operation)
        if include_hash:
            metadata['content_hash'] = self.get_file_hash(file_path)
            
        return metadata
    
    def is_file_modified(self, file_path: str) -> Tuple[bool, str]:
        """
        Check if file has been modified since last indexing
        Returns: (is_modified, status) where status is 'new', 'modified', or 'unchanged'
        """
        # Get metadata without expensive hash calculation first
        current_metadata = self.get_file_metadata(file_path, include_hash=False)
        if not current_metadata:
            return False, 'not_found'
        
        file_id = current_metadata['file_id']
        
        try:
            # Query existing metadata
            results = self.metadata_collection.get(
                ids=[file_id],
                include=['metadatas']
            )
            
            if not results['ids']:
                return True, 'new'  # File not tracked before
            
            stored_metadata = results['metadatas'][0]
            
            # Check modification time first (fastest)
            if current_metadata['mtime'] != stored_metadata.get('mtime'):
                return True, 'modified'
            
            # Check size (also fast)
            if current_metadata['size'] != stored_metadata.get('size'):
                return True, 'modified'
            
            # If mtime and size haven't changed, file is likely unchanged
            # Only calculate hash if absolutely necessary
            current_hash = self.get_file_hash(file_path)
            if current_hash != stored_metadata.get('content_hash'):
                return True, 'modified'
            
            return False, 'unchanged'
            
        except Exception as e:
            print_warning(f"Error checking file metadata: {e}")
            return True, 'new'  # Assume new if we can't check
    
    def store_file_metadata(self, file_path: str, chunk_count: int = 0):
        """Store or update file metadata in the database"""
        metadata = self.get_file_metadata(file_path)
        if not metadata:
            return False
        
        file_id = metadata['file_id']
        
        # Add chunk count to metadata
        metadata['chunk_count'] = chunk_count
        
        try:
            # Check if file already exists
            existing = self.metadata_collection.get(ids=[file_id])
            
            if existing['ids']:
                # Update existing
                self.metadata_collection.update(
                    ids=[file_id],
                    documents=[metadata['file_path']],
                    metadatas=[metadata]
                )
                print_info(f"Updated metadata for: {metadata['file_name']}")
            else:
                # Add new
                self.metadata_collection.add(
                    ids=[file_id],
                    documents=[metadata['file_path']],
                    metadatas=[metadata]
                )
                print_info(f"Added metadata for: {metadata['file_name']}")
            
            return True
            
        except Exception as e:
            print_error(f"Error storing file metadata: {e}")
            return False
    
    def get_file_chunk_count(self, file_path: str) -> int:
        """Get number of chunks for a file"""
        file_id = self.generate_file_id(file_path)
        
        try:
            results = self.metadata_collection.get(
                ids=[file_id],
                include=['metadatas']
            )
            
            if results['ids']:
                return results['metadatas'][0].get('chunk_count', 0)
            
        except Exception:
            pass
        
        return 0
    
    def remove_file_metadata(self, file_path: str) -> bool:
        """Remove file metadata from tracking"""
        file_id = self.generate_file_id(file_path)
        
        try:
            self.metadata_collection.delete(ids=[file_id])
            print_info(f"Removed metadata for: {os.path.basename(file_path)}")
            return True
        except Exception as e:
            print_warning(f"Error removing file metadata: {e}")
            return False
    
    def get_all_tracked_files(self) -> List[Dict]:
        """Get all tracked files with their metadata"""
        try:
            results = self.metadata_collection.get(include=['metadatas', 'documents'])
            
            tracked_files = []
            for i, file_id in enumerate(results['ids']):
                metadata = results['metadatas'][i]
                metadata['file_id'] = file_id
                tracked_files.append(metadata)
            
            return tracked_files
            
        except Exception as e:
            print_warning(f"Error getting tracked files: {e}")
            return []
    
    def cleanup_deleted_files(self, existing_file_paths: List[str]) -> List[str]:
        """Remove tracking for files that no longer exist"""
        tracked_files = self.get_all_tracked_files()
        existing_abs_paths = {os.path.abspath(f) for f in existing_file_paths}
        
        deleted_files = []
        for file_metadata in tracked_files:
            if file_metadata['file_path'] not in existing_abs_paths:
                file_id = file_metadata['file_id']
                try:
                    self.metadata_collection.delete(ids=[file_id])
                    deleted_files.append(file_metadata['file_path'])
                    print_info(f"Removed deleted file: {file_metadata['file_name']}")
                except Exception as e:
                    print_warning(f"Error removing deleted file metadata: {e}")
        
        return deleted_files
    
    def get_modified_files(self, file_paths: List[str]) -> Dict[str, str]:
        """
        Check multiple files for modifications
        Returns: {file_path: status} where status is 'new', 'modified', 'unchanged'
        """
        result = {}
        
        for file_path in file_paths:
            if os.path.exists(file_path):
                is_modified, status = self.is_file_modified(file_path)
                result[file_path] = status
            else:
                result[file_path] = 'not_found'
        
        return result
    
    def get_tracking_stats(self) -> Dict:
        """Get statistics about tracked files"""
        tracked_files = self.get_all_tracked_files()
        
        total_files = len(tracked_files)
        total_size = sum(f.get('size', 0) for f in tracked_files)
        total_chunks = sum(f.get('chunk_count', 0) for f in tracked_files)
        
        extensions = {}
        for file_data in tracked_files:
            ext = file_data.get('extension', 'unknown')
            extensions[ext] = extensions.get(ext, 0) + 1
        
        return {
            'total_files': total_files,
            'total_size': total_size,
            'total_chunks': total_chunks,
            'extensions': extensions
        }
    
    def print_tracking_status(self):
        """Print current file tracking status"""
        stats = self.get_tracking_stats()
        
        print_info("File Tracking Status:")
        print(f"  📁 Tracked files: {stats['total_files']}")
        print(f"  📦 Total chunks: {stats['total_chunks']}")
        print(f"  💾 Total size: {self._format_size(stats['total_size'])}")
        print(f"  📄 File types: {dict(stats['extensions'])}")
    
    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human readable format"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB"]
        i = 0
        while size_bytes >= 1024.0 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        
        return f"{size_bytes:.1f} {size_names[i]}"