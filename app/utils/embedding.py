from typing import List
import numpy as np
from openai import OpenAI
from app.core.config import settings

client = OpenAI(api_key=settings.OPENAI_API_KEY)

def get_embedding(text: str) -> List[float]:
    """
    Get embedding for text using OpenAI's API.
    """
    response = client.embeddings.create(
        model="text-embedding-ada-002",
        input=text
    )
    return response.data[0].embedding 