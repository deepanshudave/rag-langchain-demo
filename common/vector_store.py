import chromadb
import os
import uuid
from typing import List, Dict, Any, Optional
from common.config import VECTOR_CONFIG, SUCCESS_MESSAGES
from common.utils import print_info, print_warning

class VectorStore:
    def __init__(self, collection_name: str = None, persist_directory: str = None):
        self.persist_directory = persist_directory or VECTOR_CONFIG["persist_directory"]
        self.collection_name = collection_name or VECTOR_CONFIG["collection_name"]
        
        # Create directory if it doesn't exist
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client with persistence
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(name=self.collection_name)
            print(f"Loaded existing collection: {self.collection_name}")
        except ValueError:
            self.collection = self.client.create_collection(name=self.collection_name)
            print(f"Created new collection: {self.collection_name}")
    
    def add_documents(self, documents: List[str], metadatas: List[Dict[str, Any]] = None, ids: List[str] = None, file_id: str = None):
        """Add documents with optional file_id reference for tracking"""
        if ids is None:
            # Generate unique IDs for each chunk
            ids = [str(uuid.uuid4()) for _ in range(len(documents))]
        
        if metadatas is None:
            metadatas = [{"source": f"document_{i}"} for i in range(len(documents))]
        
        # Add file_id to all metadata if provided
        if file_id:
            for metadata in metadatas:
                metadata['file_id'] = file_id
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids
        )
        print(SUCCESS_MESSAGES["documents_indexed"].format(count=len(documents)))
        return ids  # Return the generated IDs
    
    def similarity_search(self, query: str, k: int = None) -> List[Dict[str, Any]]:
        k = k or VECTOR_CONFIG["similarity_search_k"]
        k = min(k, VECTOR_CONFIG["max_results"])  # Cap at max_results
        
        results = self.collection.query(
            query_texts=[query],
            n_results=k
        )
        
        # Format results
        formatted_results = []
        if results['documents'] and results['documents'][0]:
            for i in range(len(results['documents'][0])):
                formatted_results.append({
                    'content': results['documents'][0][i],
                    'metadata': results['metadatas'][0][i] if results['metadatas'][0] else {},
                    'distance': results['distances'][0][i] if results['distances'][0] else 0,
                    'id': results['ids'][0][i] if results['ids'][0] else f"doc_{i}"
                })
        
        return formatted_results
    
    def get_collection_info(self):
        """Get comprehensive collection information"""
        count = self.collection.count()
        
        # Get file_id statistics
        file_ids = set()
        try:
            # Sample some documents to get file_id info
            sample_results = self.collection.get(
                limit=min(100, count) if count > 0 else 0,
                include=['metadatas']
            )
            
            for metadata in sample_results.get('metadatas', []):
                if 'file_id' in metadata:
                    file_ids.add(metadata['file_id'])
                    
        except Exception:
            pass
        
        return {
            'name': self.collection_name,
            'count': count,
            'unique_files': len(file_ids),
            'persist_directory': self.persist_directory
        }
    
    def remove_documents_by_file_id(self, file_id: str) -> int:
        """Remove all documents associated with a specific file_id"""
        try:
            # Query documents with this file_id
            results = self.collection.get(
                where={"file_id": file_id},
                include=['ids']
            )
            
            if results['ids']:
                # Delete all chunks for this file
                self.collection.delete(ids=results['ids'])
                count = len(results['ids'])
                print_info(f"Removed {count} chunks for file_id: {file_id[:8]}...")
                return count
            else:
                print_info(f"No chunks found for file_id: {file_id[:8]}...")
                return 0
                
        except Exception as e:
            print_warning(f"Error removing documents by file_id: {e}")
            return 0
    
    def get_documents_by_file_id(self, file_id: str) -> List[Dict[str, Any]]:
        """Get all document chunks for a specific file_id"""
        try:
            results = self.collection.get(
                where={"file_id": file_id},
                include=['documents', 'metadatas', 'ids']
            )
            
            formatted_results = []
            if results['ids']:
                for i, doc_id in enumerate(results['ids']):
                    formatted_results.append({
                        'id': doc_id,
                        'content': results['documents'][i],
                        'metadata': results['metadatas'][i]
                    })
            
            return formatted_results
            
        except Exception as e:
            print_warning(f"Error getting documents by file_id: {e}")
            return []
    
    def clear_collection(self):
        """Clear the entire collection"""
        self.client.delete_collection(name=self.collection_name)
        self.collection = self.client.create_collection(name=self.collection_name)
        print(f"Cleared collection: {self.collection_name}")