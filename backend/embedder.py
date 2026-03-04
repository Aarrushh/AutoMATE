from typing import List
from sentence_transformers import SentenceTransformer

try:
    from .schema import AutomationTemplate
except ImportError:
    from schema import AutomationTemplate

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """
        Initializes the EmbeddingService with a sentence-transformer model.
        Default is 'all-MiniLM-L6-v2' for a good balance of speed and performance.
        """
        self.model = SentenceTransformer(model_name)

    def generate_embedding_text(self, template: AutomationTemplate) -> str:
        """
        Constructs a highly contextual string for embedding from an AutomationTemplate.
        """
        actions_str = ", ".join(template.action_apps)
        return (
            f"Trigger: {template.trigger_app}. "
            f"Actions: {actions_str}. "
            f"Description: {template.description}. "
            f"Complexity: {template.complexity_score}/5. "
            f"OPEX: ${template.monthly_opex}."
        )

    def embed_template(self, template: AutomationTemplate) -> List[float]:
        """
        Generates a vector embedding for a single AutomationTemplate.
        """
        text = self.generate_embedding_text(template)
        embedding = self.model.encode(text)
        return embedding.tolist()

    def embed_templates_batch(self, templates: List[AutomationTemplate], batch_size: int = 100) -> List[List[float]]:
        """
        Generates vector embeddings for a list of AutomationTemplates in batches.
        """
        all_embeddings = []
        for i in range(0, len(templates), batch_size):
            batch = templates[i : i + batch_size]
            texts = [self.generate_embedding_text(t) for t in batch]
            batch_embeddings = self.model.encode(texts)
            all_embeddings.extend(batch_embeddings.tolist())
        return all_embeddings
