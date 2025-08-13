from langchain_community.document_loaders import PyPDFLoader, TextLoader, DirectoryLoader
from langchain.schema import Document
from typing import List
import os
import glob
from common.config import DOCUMENT_CONFIG

class DocumentLoader:
    def __init__(self, documents_path: str = None):
        self.documents_path = documents_path or DOCUMENT_CONFIG["documents_directory"]
        os.makedirs(self.documents_path, exist_ok=True)
    
    def load_pdf(self, file_path: str) -> List[Document]:
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        print(f"Loaded {len(documents)} pages from PDF: {file_path}")
        return documents
    
    def load_text(self, file_path: str) -> List[Document]:
        loader = TextLoader(file_path)
        documents = loader.load()
        print(f"Loaded text file: {file_path}")
        return documents
    
    def load_directory(self, directory_path: str = None) -> List[Document]:
        if directory_path is None:
            directory_path = self.documents_path
        
        documents = []
        
        # Load PDF files
        pdf_files = glob.glob(os.path.join(directory_path, "*.pdf"))
        for pdf_file in pdf_files:
            try:
                pdf_docs = self.load_pdf(pdf_file)
                documents.extend(pdf_docs)
            except Exception as e:
                print(f"Error loading PDF {pdf_file}: {e}")
        
        # Load text files
        txt_files = glob.glob(os.path.join(directory_path, "*.txt"))
        for txt_file in txt_files:
            try:
                txt_docs = self.load_text(txt_file)
                documents.extend(txt_docs)
            except Exception as e:
                print(f"Error loading text file {txt_file}: {e}")
        
        print(f"Total documents loaded from directory: {len(documents)}")
        return documents
    
    def load_from_text(self, text: str, metadata: dict = None) -> List[Document]:
        if metadata is None:
            metadata = {"source": "user_input"}
        
        doc = Document(page_content=text, metadata=metadata)
        return [doc]