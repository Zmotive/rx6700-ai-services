#!/usr/bin/env python3
"""
Qwen2.5-Coder Service - Python Client Wrapper
Provides a simple Python interface to the Ollama-based Qwen2.5-Coder model
"""

import requests
from typing import Optional, Dict, Any, Iterator
import json


class QwenCoderClient:
    """Client for interacting with Qwen2.5-Coder via Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:8001"):
        self.base_url = base_url
        self.model = "qwen2.5-coder:7b"
    
    def generate(
        self, 
        prompt: str, 
        system: Optional[str] = None,
        stream: bool = False,
        temperature: float = 0.7,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate code or text completion
        
        Args:
            prompt: The input prompt
            system: Optional system prompt
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0-1.0)
            **kwargs: Additional Ollama parameters
        
        Returns:
            Response dictionary with 'response' and metadata
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": stream,
            "options": {
                "temperature": temperature,
                **kwargs
            }
        }
        
        if system:
            payload["system"] = system
        
        response = requests.post(
            f"{self.base_url}/api/generate",
            json=payload
        )
        response.raise_for_status()
        
        if stream:
            return self._stream_response(response)
        else:
            return response.json()
    
    def chat(
        self,
        messages: list,
        stream: bool = False,
        **kwargs
    ) -> Dict[str, Any]:
        """
        OpenAI-compatible chat completion
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            stream: Whether to stream the response
            **kwargs: Additional parameters
        
        Returns:
            Response dictionary
        """
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            **kwargs
        }
        
        response = requests.post(
            f"{self.base_url}/v1/chat/completions",
            json=payload
        )
        response.raise_for_status()
        return response.json()
    
    def _stream_response(self, response: requests.Response) -> Iterator[str]:
        """Handle streaming responses"""
        for line in response.iter_lines():
            if line:
                data = json.loads(line)
                yield data.get("response", "")
                if data.get("done"):
                    break
    
    def health_check(self) -> bool:
        """Check if the service is healthy"""
        try:
            response = requests.get(f"{self.base_url}/")
            return response.status_code == 200
        except:
            return False


# Example usage
if __name__ == "__main__":
    print("�� Qwen2.5-Coder Client Example")
    print("-" * 50)
    
    # Initialize client
    client = QwenCoderClient()
    
    # Check health
    if not client.health_check():
        print("❌ Service is not available")
        print("Make sure the qwen-coder service is running:")
        print("  cd ~/ai-workspace/services/qwen-coder")
        print("  docker compose up -d")
        exit(1)
    
    print("✓ Service is healthy\n")
    
    # Example 1: Simple code generation
    print("Example 1: Generate a Python function")
    print("-" * 50)
    result = client.generate(
        prompt="Write a Python function to reverse a linked list",
        system="You are an expert Python developer. Provide clean, well-documented code.",
        temperature=0.7
    )
    print(result["response"])
    print()
    
    # Example 2: Chat-based interaction
    print("\nExample 2: Chat completion")
    print("-" * 50)
    chat_result = client.chat(
        messages=[
            {"role": "system", "content": "You are a helpful coding assistant."},
            {"role": "user", "content": "How do I implement a binary search in Python?"}
        ]
    )
    print(chat_result)
