import uuid
import sys
import os

# Add the current directory to sys.path to allow imports without '.'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from schema import AutomationTemplate, MaintenanceLevel
from embedder import EmbeddingService

def test_embedding_service():
    # 1. Setup mock data
    template1 = AutomationTemplate(
        id=uuid.uuid4(),
        title="Gmail to Slack",
        description="Notify Slack when a new email arrives in Gmail",
        source_url="https://example.com/1",
        source_platform="Zapier",
        trigger_app="Gmail",
        action_apps=["Slack"],
        complexity_score=2,
        maintenance_level=MaintenanceLevel.LOW,
        monthly_opex=0.0,
        raw_data={}
    )

    template2 = AutomationTemplate(
        id=uuid.uuid4(),
        title="Webhooks to Google Sheets and Discord",
        description="Log webhook data to Sheets and notify Discord",
        source_url="https://example.com/2",
        source_platform="Make",
        trigger_app="Webhooks",
        action_apps=["Google Sheets", "Discord"],
        complexity_score=3,
        maintenance_level=MaintenanceLevel.MEDIUM,
        monthly_opex=5.0,
        raw_data={}
    )

    # 2. Initialize service
    print("Initializing EmbeddingService...")
    service = EmbeddingService()

    # 3. Test text generation
    text1 = service.generate_embedding_text(template1)
    print(f"Generated text 1: {text1}")
    assert "Trigger: Gmail" in text1
    assert "Actions: Slack" in text1

    text2 = service.generate_embedding_text(template2)
    print(f"Generated text 2: {text2}")
    assert "Trigger: Webhooks" in text2
    assert "Actions: Google Sheets, Discord" in text2

    # 4. Test single embedding
    print("Testing single embedding...")
    vec1 = service.embed_template(template1)
    print(f"Vector size: {len(vec1)}")
    assert isinstance(vec1, list)
    assert len(vec1) > 0

    # 5. Test batch embedding
    print("Testing batch embedding...")
    templates = [template1, template2]
    vectors = service.embed_templates_batch(templates, batch_size=1)
    print(f"Batch vector size: {len(vectors)}")
    assert len(vectors) == 2
    assert len(vectors[0]) == len(vec1)

    print("All tests passed!")

if __name__ == "__main__":
    try:
        test_embedding_service()
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
