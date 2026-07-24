# Omnix V4 module
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger
from system.resource_manager import ResourceManager


class MemoryManager:

    def __init__(self):

        logger.info("Initializing Memory Manager")

        # embedding model

        self.model = ResourceManager.get_instance().get_embedding_model()

        self.dimension = 384

        self.index = faiss.IndexFlatL2(self.dimension)

        self.memories = []

    def add_memory(self, text):

        try:

            embedding = self.model.encode([text])

            vector = np.array(embedding).astype("float32")

            self.index.add(vector)

            self.memories.append(text)

            logger.info(f"Memory stored: {text}")

        except Exception as e:

            logger.error(f"Memory store failed: {e}")

    def search_memory(self, query, top_k=3):

        try:

            if len(self.memories) == 0:
                return []

            embedding = self.model.encode([query])

            vector = np.array(embedding).astype("float32")

            distances, indices = self.index.search(
                vector, min(top_k, len(self.memories)))

            results = []

            for i in indices[0]:

                if 0 <= i < len(self.memories):
                    results.append(self.memories[i])

            return results

        except Exception as e:

            logger.error(f"Memory search failed: {e}")

            return []
