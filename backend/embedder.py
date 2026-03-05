from typing import List

class EmbeddingService:
    def __init__(self):
        # Mocking for now as per requirements
        pass

    def get_embedding(self, text: str) -> List[float]:
        # Return a dummy vector of 384 dimensions (all-MiniLM-L6-v2 size)
        return [0.1] * 384

    def embed_templates_batch(self, templates: List[any], batch_size: int = 100):
        # Mock implementation
        pass
