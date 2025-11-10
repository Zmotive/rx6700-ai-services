#!/usr/bin/env python3
"""
Dia TTS Client
Python wrapper for the Dia TTS API
"""

import requests
import base64
from typing import Optional, Literal
from pathlib import Path


class DiaClient:
    """Client for interacting with Dia TTS API"""
    
    def __init__(self, base_url: str = "http://localhost:8002"):
        """
        Initialize Dia client
        
        Args:
            base_url: Base URL of the Dia API server
        """
        self.base_url = base_url.rstrip('/')
    
    def health_check(self) -> dict:
        """
        Check API health status
        
        Returns:
            Health status information
        """
        response = requests.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def generate(
        self,
        text: str,
        cfg_scale: float = 3.0,
        temperature: float = 1.8,
        top_p: float = 0.90,
        top_k: int = 45,
        seed: Optional[int] = None,
        output_format: Literal["mp3", "wav", "base64"] = "mp3",
        save_path: Optional[str] = None
    ) -> dict:
        """
        Generate dialogue audio from text
        
        Args:
            text: Text with speaker tags [S1] and [S2]
            cfg_scale: Classifier-free guidance scale (1.0-10.0)
            temperature: Sampling temperature (0.1-2.5)
            top_p: Nucleus sampling threshold (0.0-1.0)
            top_k: Top-k filtering (1-100)
            seed: Random seed for reproducibility
            output_format: Output format (mp3, wav, or base64)
            save_path: If provided, save audio to this path
        
        Returns:
            Response with audio data or metadata
        """
        payload = {
            "text": text,
            "cfg_scale": cfg_scale,
            "temperature": temperature,
            "top_p": top_p,
            "top_k": top_k,
            "output_format": output_format
        }
        
        if seed is not None:
            payload["seed"] = seed
        
        response = requests.post(
            f"{self.base_url}/generate",
            json=payload
        )
        response.raise_for_status()
        
        # Handle different output formats
        if output_format == "base64":
            result = response.json()
            
            # Optionally save to file
            if save_path:
                audio_data = base64.b64decode(result["audio_base64"])
                with open(save_path, 'wb') as f:
                    f.write(audio_data)
                print(f"✅ Audio saved to {save_path}")
            
            return result
        else:
            # Binary audio response
            if save_path:
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                print(f"✅ Audio saved to {save_path}")
            
            return {
                "message": "Audio generated successfully",
                "content_type": response.headers.get('content-type'),
                "size_bytes": len(response.content)
            }
    
    def list_nonverbals(self) -> dict:
        """
        List supported non-verbal sound effects
        
        Returns:
            Dictionary with list of non-verbal tags
        """
        response = requests.get(f"{self.base_url}/nonverbals")
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    import sys
    
    print("Dia TTS Client - Example Usage")
    print("=" * 50)
    
    # Initialize client
    client = DiaClient()
    
    # Check health
    print("\n1. Health Check:")
    print("-" * 50)
    try:
        health = client.health_check()
        print(f"Status: {health['status']}")
        print(f"Model loaded: {health['model_loaded']}")
        print(f"Device: {health['device']}")
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # List non-verbals
    print("\n2. Available Non-verbal Sound Effects:")
    print("-" * 50)
    nonverbals = client.list_nonverbals()
    print(f"Supported: {', '.join(nonverbals['nonverbals'][:10])}...")
    print(f"Total: {len(nonverbals['nonverbals'])} effects")
    
    # Generate dialogue
    print("\n3. Generate Dialogue:")
    print("-" * 50)
    text = "[S1] Hey! How's it going? [S2] I'm doing great! (laughs) [S1] That's wonderful to hear! (chuckle)"
    print(f"Input: {text}")
    
    result = client.generate(
        text=text,
        output_format="mp3",
        save_path="example_dialogue.mp3"
    )
    print(f"Output: {result}")
    
    # Generate with sound effects
    print("\n4. Generate with More Sound Effects:")
    print("-" * 50)
    text_sfx = "[S1] (clears throat) Attention everyone! [S2] (gasps) What is it? [S1] (sighs) Never mind."
    print(f"Input: {text_sfx}")
    
    result = client.generate(
        text=text_sfx,
        temperature=1.5,  # Lower temperature for more consistent output
        save_path="example_sound_effects.mp3"
    )
    print(f"Output: {result}")
    
    print("\n✅ Examples completed!")
    print("Generated files: example_dialogue.mp3, example_sound_effects.mp3")
