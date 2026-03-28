import json
import logging
import os
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

CLEAN_TEMPLATES_FILE = "backend/processed_data/clean_templates.json"
VECTOR_STORE_DIR = "backend/vector_store"

class PipelineEmbedder:
    def __init__(self):
        os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
        self.client = chromadb.PersistentClient(path=VECTOR_STORE_DIR)
        self.model_name = "all-MiniLM-L6-v2"
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=self.model_name)
        self.collection = self.client.get_or_create_collection(
            name="automation_templates",
            embedding_function=self.embedding_fn
        )

    def load_clean_data(self):
        if not os.path.exists(CLEAN_TEMPLATES_FILE):
            logger.error(f"{CLEAN_TEMPLATES_FILE} not found. Run cleaner first.")
            return []
        with open(CLEAN_TEMPLATES_FILE, 'r') as f:
            return json.load(f)

    def generate_embeddings(self, templates):
        logger.info(f"Generating embeddings for {len(templates)} templates...")

        ids = []
        documents = []
        metadatas = []

        for t in templates:
            # Concatenate name + description + apps
            apps_str = ", ".join(t.get('action_apps', []))
            doc_str = f"Name: {t.get('name')} | Description: {t.get('description')} | Tools: {apps_str}"

            ids.append(str(t.get('id')))
            documents.append(doc_str)
            metadatas.append({
                "source": t.get('source_platform'),
                "url": t.get('url') or "",
                "name": t.get('name')
            })

        # Batch add to ChromaDB
        batch_size = 100
        for i in range(0, len(ids), batch_size):
            end = i + batch_size
            self.collection.add(
                ids=ids[i:end],
                documents=documents[i:end],
                metadatas=metadatas[i:end]
            )
            logger.info(f"Embedded {end} / {len(ids)} templates")

if __name__ == "__main__":
    embedder = PipelineEmbedder()
    templates = embedder.load_clean_data()
    if templates:
        embedder.generate_embeddings(templates)
        logger.info("Local Vectorization complete.")
