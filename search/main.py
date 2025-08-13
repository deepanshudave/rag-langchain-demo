#!/usr/bin/env python3

"""
Search and Query Module for RAG System
Handles document retrieval and response generation
"""

from common.vector_store import VectorStore
from search.rag_chain import RAGChain
from common.utils import (
    load_environment, check_api_key, validate_query,
    print_section_header, print_success, print_error, truncate_text
)
from common.config import VECTOR_CONFIG, ERROR_MESSAGES

class DocumentSearcher:
    def __init__(self, collection_name: str = None):
        load_environment()
        
        # Initialize components
        self.vector_store = VectorStore(collection_name=collection_name)
        self.rag_chain = RAGChain()
        
        print("Document Searcher initialized successfully!")
    
    def search_documents(self, query: str, k: int = None):
        """Search for relevant documents with adaptive retrieval count"""
        if not validate_query(query):
            return []
        
        print_section_header("Searching Documents")
        print(f"Query: {truncate_text(query, 100)}")
        
        # Determine search complexity and adjust retrieval count
        if k is None:
            is_complex = len(query.split()) > 10 or any(word in query.lower() 
                                                      for word in ['compare', 'analyze', 'explain', 'detailed', 'comprehensive'])
            k = VECTOR_CONFIG.get("similarity_search_k_complex", 5) if is_complex else VECTOR_CONFIG["similarity_search_k"]
        
        # Retrieve relevant documents
        retrieved_docs = self.vector_store.similarity_search(query, k=k)
        
        if not retrieved_docs:
            print_error("No relevant documents found!")
            return []
        
        print(f"Found {len(retrieved_docs)} relevant documents (k={k})")
        return retrieved_docs
    
    def ask_question(self, question: str, k: int = None):
        """Ask a question and get an AI-generated response"""
        if not validate_query(question):
            return None
        
        # Check if API key is set
        if not check_api_key():
            return None
        
        print_section_header("Processing Question")
        print(f"Question: {truncate_text(question, 100)}")
        
        # Search for relevant documents
        retrieved_docs = self.search_documents(question, k=k)
        
        if not retrieved_docs:
            print_error("No relevant information found to answer the question.")
            return None
        
        # Generate response with complexity detection
        print("Generating AI response...")
        is_complex = len(question.split()) > 10 or any(word in question.lower() 
                                                      for word in ['compare', 'analyze', 'explain', 'detailed', 'comprehensive'])
        response = self.rag_chain.generate_response(question, retrieved_docs, is_complex=is_complex)
        
        return {
            'question': question,
            'answer': response,
            'sources': retrieved_docs,
            'num_sources': len(retrieved_docs)
        }
    
    def show_search_results(self, query: str, k: int = None):
        """Show detailed search results without AI generation"""
        results = self.search_documents(query, k=k)
        
        if not results:
            return
        
        print_section_header("Search Results")
        for i, doc in enumerate(results, 1):
            print(f"\n--- Document {i} ---")
            print(f"Source: {doc.get('metadata', {}).get('source', 'Unknown')}")
            print(f"Distance: {doc.get('distance', 'N/A'):.4f}")
            print(f"Content Preview: {truncate_text(doc['content'], 200)}")
    
    def get_collection_info(self):
        """Get information about the indexed collection"""
        info = self.vector_store.get_collection_info()
        print_section_header("Collection Status")
        print(f"Collection: {info['name']}")
        print(f"Total chunks: {info['count']}")
        print(f"Storage location: {info['persist_directory']}")
        
        # Model info
        model_info = self.rag_chain.get_model_info()
        print(f"Model: {model_info['model_name']}")
        print(f"Provider: {model_info['provider']}")
        print(f"API Key: {'✅ Set' if model_info['api_key_set'] else '❌ Missing'}")
        
        return info
    
    def interactive_search(self):
        """Interactive search session"""
        print("\n🔍 Interactive Search Mode")
        print("Type 'quit' or 'exit' to stop\n")
        
        while True:
            try:
                question = input("Ask a question: ").strip()
                
                if question.lower() in ['quit', 'exit', '']:
                    print("Goodbye!")
                    break
                
                result = self.ask_question(question)
                
                if result:
                    print_success(f"Answer: {result['answer']}")
                    print(f"📚 Based on {result['num_sources']} source(s)")
                else:
                    print_error("Could not generate an answer.")
                
                print("\n" + "="*50)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {str(e)}")

def main():
    """Command line interface for searching"""
    import sys
    
    searcher = DocumentSearcher()
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python searcher.py ask \"<question>\"      - Ask a question")
        print("  python searcher.py search \"<query>\"       - Search documents")
        print("  python searcher.py interactive            - Interactive mode")
        print("  python searcher.py status                - Show collection status")
        return
    
    command = sys.argv[1].lower()
    
    if command == "ask":
        if len(sys.argv) < 3:
            print("Error: Question required")
            return
        
        question = " ".join(sys.argv[2:])
        result = searcher.ask_question(question)
        
        if result:
            print(f"\nQuestion: {result['question']}")
            print(f"Answer: {result['answer']}")
    
    elif command == "search":
        if len(sys.argv) < 3:
            print("Error: Search query required")
            return
        
        query = " ".join(sys.argv[2:])
        searcher.show_search_results(query)
    
    elif command == "interactive":
        searcher.interactive_search()
    
    elif command == "status":
        searcher.get_collection_info()
    
    else:
        print(f"Unknown command: {command}")

if __name__ == "__main__":
    main()