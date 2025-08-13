import anthropic
from typing import List, Dict, Any
import os
from common.config import MODEL_CONFIG, PROMPTS, API_CONFIG, ERROR_MESSAGES

class RAGChain:
    def __init__(self, model_name: str = None, temperature: float = None):
        self.model_name = model_name or MODEL_CONFIG["name"]
        self.temperature = temperature or MODEL_CONFIG["temperature"]
        
        # Get API key
        api_key = os.getenv(API_CONFIG["anthropic_api_key_env"])
        if not api_key:
            raise ValueError(f"Missing {API_CONFIG['anthropic_api_key_env']} environment variable")
        
        # Initialize the Anthropic client with current API
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def format_context(self, retrieved_docs: List[Dict[str, Any]]) -> str:
        context_parts = []
        
        for i, doc in enumerate(retrieved_docs, 1):
            content = doc['content']
            metadata = doc.get('metadata', {})
            source = metadata.get('source', 'Unknown source')
            
            context_part = PROMPTS["context_format"].format(
                index=i,
                source=source,
                content=content
            )
            context_parts.append(context_part)
        
        return "\n".join(context_parts)
    
    def generate_response(self, question: str, retrieved_docs: List[Dict[str, Any]], 
                         is_complex: bool = False) -> str:
        # Format the context from retrieved documents
        context = self.format_context(retrieved_docs)
        
        # Estimate token usage and choose appropriate limits
        estimated_tokens = len(context.split()) + len(question.split())
        max_tokens = (MODEL_CONFIG.get("max_tokens_complex", 1200) 
                     if is_complex or estimated_tokens > 300 
                     else MODEL_CONFIG.get("max_tokens", 800))
        
        # Use current Messages API
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=max_tokens,
                temperature=self.temperature,
                system=PROMPTS["system_prompt"],
                messages=[
                    {"role": "user", "content": PROMPTS["human_prompt"].format(context=context, question=question)}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def generate_standalone_response(self, question: str) -> str:
        # For questions without context (direct LLM usage)
        try:
            message = self.client.messages.create(
                model=self.model_name,
                max_tokens=MODEL_CONFIG.get("max_tokens", 1000),
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": PROMPTS["standalone_prompt"].format(question=question)}
                ]
            )
            
            return message.content[0].text
        except Exception as e:
            return f"Error generating response: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        return {
            'model_name': self.model_name,
            'temperature': self.temperature,
            'max_tokens': MODEL_CONFIG["max_tokens"],
            'provider': 'Anthropic Claude',
            'api_key_set': bool(os.getenv(API_CONFIG["anthropic_api_key_env"]))
        }