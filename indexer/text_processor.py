from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from typing import List
from common.config import TEXT_CONFIG

class TextProcessor:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize text splitter
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap,
            length_function=len,
            separators=TEXT_CONFIG["separators"]
        )
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        chunked_docs = self.text_splitter.split_documents(documents)
        
        # Add chunk information to metadata
        for i, chunk in enumerate(chunked_docs):
            if 'chunk_id' not in chunk.metadata:
                chunk.metadata['chunk_id'] = i
                chunk.metadata['chunk_size'] = len(chunk.page_content)
        
        print(f"Split {len(documents)} documents into {len(chunked_docs)} chunks")
        return chunked_docs
    
    def chunk_text(self, text: str, metadata: dict = None) -> List[Document]:
        if metadata is None:
            metadata = {}
        
        # Create document from text
        doc = Document(page_content=text, metadata=metadata)
        
        # Split into chunks
        chunks = self.text_splitter.split_documents([doc])
        
        # Add chunk information
        for i, chunk in enumerate(chunks):
            chunk.metadata.update({
                'chunk_id': i,
                'chunk_size': len(chunk.page_content),
                'original_length': len(text)
            })
        
        print(f"Split text into {len(chunks)} chunks")
        return chunks
    
    def preprocess_text(self, text: str) -> str:
        # Basic text preprocessing
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Remove empty lines and normalize spacing
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text
    
    def extract_text_from_chunks(self, chunks: List[Document]) -> List[str]:
        return [chunk.page_content for chunk in chunks]
    
    def get_chunk_metadata(self, chunks: List[Document]) -> List[dict]:
        return [chunk.metadata for chunk in chunks]