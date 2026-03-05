from sentence_transformers import SentenceTransformer
from .schema import AutomationTemplate

class EmbeddingService:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def generate_text_for_embedding(self, template: AutomationTemplate) -> str:
        actions = ", ".join(template.action_apps)
        return f"Trigger: {template.trigger_app}. Actions: {actions}. Description: {template.description}. Complexity: {template.complexity_score}/5. OPEX: ${template.monthly_opex}."

    def get_embedding(self, text: str):
        return self.model.encode(text).tolist()

    def embed_templates_batch(self, templates: list[AutomationTemplate]):
        texts = [self.generate_text_for_embedding(t) for t in templates]
        return self.model.encode(texts).tolist()
