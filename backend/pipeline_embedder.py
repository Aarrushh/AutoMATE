import json
import os
import logging
import faiss
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
PROCESSED_FILE = Path("data/processed_templates.json")
VECTOR_DB_DIR = Path("backend/vector_db")
VECTOR_DB_DIR.mkdir(exist_ok=True, parents=True)
INDEX_FILE = VECTOR_DB_DIR / "templates.index"
METADATA_FILE = VECTOR_DB_DIR / "metadata.json"

def run_embedder():
    """
    ETL Step 3: Generate vector embeddings and store in FAISS.
    """
    if not PROCESSED_FILE.exists():
        logger.error(f"Processed file not found: {PROCESSED_FILE}")
        return

    logger.info(f"Loading processed templates from {PROCESSED_FILE}")
    with open(PROCESSED_FILE, "r") as f:
        templates = json.load(f)

    if not templates:
        logger.warning("No templates to embed.")
        return

    # Initialize model
    logger.info("Initializing SentenceTransformer model: all-MiniLM-L6-v2")
    model = SentenceTransformer('all-MiniLM-L6-v2')

    # Prepare texts for embedding (Name + Description)
    texts = [f"{t['name']} {t['description']}" for t in templates]

    logger.info(f"Generating embeddings for {len(texts)} templates...")
    embeddings = model.encode(texts, show_progress_bar=True)

    # Convert to float32 for FAISS
    embeddings = np.array(embeddings).astype('float32')

    # Initialize FAISS index
    dimension = embeddings.shape[1]
    index = faiss.IndexFlatL2(dimension)
    index.add(embeddings)

    # Save index
    faiss.write_index(index, str(INDEX_FILE))

    # Save metadata (to map index back to template details)
    metadata = []
    for t in templates:
        metadata.append({
            "id": t["id"],
            "name": t["name"],
            "source_platform": t["source_platform"]
        })

    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Successfully created FAISS index and metadata at {VECTOR_DB_DIR}")

if __name__ == "__main__":
    run_embedder()
