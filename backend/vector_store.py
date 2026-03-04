from typing import List
try:
    from .schema import AutomationTemplate
except ImportError:
    from schema import AutomationTemplate

def upsert_templates(templates: List[AutomationTemplate], embeddings: List[List[float]]):
    """
    Constructs the vector payload for upserting into a Vector DB (default: Pinecone).

    Args:
        templates: List of AutomationTemplate objects.
        embeddings: List of embedding vectors corresponding to the templates.

    Returns:
        List[dict]: A list of payloads ready for Pinecone upsert.
    """
    if len(templates) != len(embeddings):
        raise ValueError("The number of templates and embeddings must match.")

    payloads = []
    for template, embedding in zip(templates, embeddings):
        payload = {
            "id": str(template.id),
            "values": embedding,
            "metadata": {
                "trigger_app": template.trigger_app,
                "action_apps": template.action_apps,
                "complexity_score": template.complexity_score,
                "maintenance_level": str(template.maintenance_level.value) if hasattr(template.maintenance_level, 'value') else str(template.maintenance_level),
                "monthly_opex": float(template.monthly_opex),
                "title": template.title,
                "source_platform": template.source_platform,
                "source_url": template.source_url
            }
        }
        payloads.append(payload)

    # In a real scenario, you would use the Pinecone client here:
    # index.upsert(vectors=payloads)

    return payloads
