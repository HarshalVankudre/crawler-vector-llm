import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")

# Embedding config
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1536"))
EMBEDDING_BATCH_SIZE = int(os.getenv("EMBEDDING_BATCH_SIZE", "100"))

# Crawler settings
DEFAULT_POLITE_DELAY_SECONDS = float(os.getenv("DEFAULT_POLITE_DELAY_SECONDS", "2.0"))
CRAWLER_USER_AGENT = os.getenv(
    "CRAWLER_USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
)
PAGE_LOAD_TIMEOUT = int(os.getenv("PAGE_LOAD_TIMEOUT", "20"))
JS_CHUNK_SIZE = int(os.getenv("JS_CHUNK_SIZE", "1000"))  # char-based chunking to mirror original logic
