"""LLM client for Gemini API integration."""
import os
from dotenv import load_dotenv
import httpx
from typing import Optional

# Load .env file
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")


def generate_with_gemini(prompt: str, max_tokens: int = 1024, temperature: float = 0.7) -> Optional[str]:
    """Call Google Gemini API (v1beta) and return text response."""
    if not GEMINI_API_KEY:
        return None
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    
    payload = {
        "contents": [
            {
                "parts": [
                    {"text": prompt}
                ]
            }
        ],
        "generationConfig": {
            "maxOutputTokens": max_tokens,
            "temperature": temperature
        }
    }
    
    try:
        with httpx.Client(timeout=30.0) as client:
            resp = client.post(url, json=payload)
            resp.raise_for_status()
            data = resp.json()
            # Extract text from response
            candidates = data.get("candidates", [])
            if candidates:
                content = candidates[0].get("content", {})
                parts = content.get("parts", [])
                if parts:
                    return parts[0].get("text", "")
    except Exception as e:
        print(f"Gemini API error: {e}")
    return None


def generate_response(prompt: str) -> str:
    """Generate response using Gemini if configured, else return fallback."""
    if GEMINI_API_KEY:
        out = generate_with_gemini(prompt)
        if out:
            return out

    # Return None to indicate LLM failed - caller should handle fallback
    return None
