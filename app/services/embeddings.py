import os
import openai
from typing import List


def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception("OPENAI_API_KEY no encontrada en las variables de entorno")
    return openai.OpenAI(api_key=api_key, timeout=30)


def embed_text(text: str) -> List[float]:
    """Genera un embedding para un texto usando OpenAI embeddings.

    Returns:
        lista de floats (embedding)
    """
    client = get_openai_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding


def embed_texts(texts: List[str]) -> List[List[float]]:
    """Genera embeddings para una lista de textos (batch)."""
    client = get_openai_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=texts
    )
    return [item.embedding for item in response.data]
