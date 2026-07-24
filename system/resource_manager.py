from sentence_transformers import SentenceTransformer
from loguru import logger


class ResourceManager:

    _instance = None

    def __init__(self):

        logger.info("Initializing Resource Manager")

        self.embedding_model = None

    @classmethod
    def get_instance(cls):

        if cls._instance is None:
            cls._instance = ResourceManager()

        return cls._instance

    def get_embedding_model(self):

        if self.embedding_model is None:

            logger.info("Loading embedding model (only once)...")

            self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

        return self.embedding_model