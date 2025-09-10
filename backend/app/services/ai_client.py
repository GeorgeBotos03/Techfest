import os
from typing import Optional

_openai_client = None
_openai_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

def get_openai_client():
    """Returnează clientul OpenAI sau None dacă nu există cheie."""
    global _openai_client
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None, None
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=key)
    return _openai_client, _openai_model
