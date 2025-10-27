import time
import hashlib
import streamlit as st
from pinecone import ServerlessSpec

from src.embeddings.clients import get_openai_client, get_pinecone_client
from src.config import (
    EMBEDDING_MODEL, EMBEDDING_DIMENSION, EMBEDDING_BATCH_SIZE, JS_CHUNK_SIZE
)

def _init_pinecone_index(pc, index_name: str):
    try:
        existing = [idx.name for idx in pc.list_indexes()]
    except Exception:
        existing = []
    if index_name not in existing:
        try:
            pc.create_index(
                name=index_name,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )
            # Wait best-effort for readiness
            for _ in range(60):
                try:
                    desc = pc.describe_index(index_name)
                    ready = getattr(getattr(desc, 'status', None), 'ready', None)
                    if ready is True:
                        break
                except Exception:
                    pass
                time.sleep(2)
        except Exception as e:
            return None, f"❌ Error creating Pinecone index: {e}"
    try:
        return pc.Index(index_name), None
    except Exception as e:
        return None, f"❌ Error opening Pinecone index: {e}"

def _chunk_text_char_based(text: str, source_url: str, max_chars: int = JS_CHUNK_SIZE):
    chunks, buf = [], ""
    for line in (text or "").splitlines():
        if len(buf) + len(line) + 1 > max_chars:
            if buf.strip():
                chunks.append({ "text": buf.strip(), "source": source_url })
            buf = line
        else:
            buf += ("\n" if buf else "") + line
    if buf.strip():
        chunks.append({ "text": buf.strip(), "source": source_url })
    return chunks

def embed_and_upload(crawled_data: dict, index_name: str):
    """Embeds and uploads crawled data to Pinecone, yielding status strings."""
    openai_client = get_openai_client()
    pinecone_client = get_pinecone_client()
    if not openai_client or not pinecone_client:
        yield "❌ Error: OpenAI or Pinecone client not initialized. Check API keys."
        return

    yield "Connecting to Pinecone and creating index (if needed)..."
    index, err = _init_pinecone_index(pinecone_client, index_name)
    if err:
        yield err
        return
    if index is None:
        yield "❌ Failed to initialize Pinecone index."
        return

    if st.session_state.get('stop_pressed'):
        yield "🛑 UPLOAD STOPPED BY USER."
        return

    yield "Chunking all text data..."
    all_chunks = []
    for url, text in (crawled_data or {}).items():
        all_chunks.extend(_chunk_text_char_based(text, url))
    yield f"Created {len(all_chunks)} text chunks."
    if not all_chunks:
        yield "⚠️ No text chunks to embed. Stopping."
        return

    yield "Embedding and uploading in batches..."
    total_batches = (len(all_chunks) + EMBEDDING_BATCH_SIZE - 1) // EMBEDDING_BATCH_SIZE

    for i in range(0, len(all_chunks), EMBEDDING_BATCH_SIZE):
        if st.session_state.get('stop_pressed'):
            yield "🛑 UPLOAD STOPPED BY USER."
            break

        batch = all_chunks[i:i + EMBEDDING_BATCH_SIZE]
        texts = [c['text'] for c in batch]

        try:
            res = openai_client.embeddings.create(input=texts, model=EMBEDDING_MODEL)
            embeddings = [d.embedding for d in res.data]

            vectors = []
            for j, c in enumerate(batch):
                chunk_id = f"{c['source']}-{hashlib.md5(c['text'].encode()).hexdigest()}"
                vectors.append({
                    "id": chunk_id,
                    "values": embeddings[j],
                    "metadata": { "source": c['source'], "text": c['text'] },
                })

            index.upsert(vectors=vectors)
            yield f"Uploaded batch {i // EMBEDDING_BATCH_SIZE + 1} / {total_batches}"
        except Exception as e:
            yield f"❌ Error processing batch {i // EMBEDDING_BATCH_SIZE + 1}: {e}"
            continue

    if not st.session_state.get('stop_pressed'):
        yield f"✅ Successfully uploaded {len(all_chunks)} vectors to '{index_name}'."
