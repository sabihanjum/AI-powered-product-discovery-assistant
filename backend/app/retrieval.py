from typing import List, Dict, Any, Tuple
import numpy as np
from sentence_transformers import SentenceTransformer
from .database import SessionLocal
from . import models

_EMBED_MODEL = None


def get_embedding_model(name: str = "all-MiniLM-L6-v2"):
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        _EMBED_MODEL = SentenceTransformer(name)
    return _EMBED_MODEL


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    embs = model.encode(texts, show_progress_bar=False, convert_to_numpy=True)
    return [e.tolist() for e in embs]


def chunk_text(text: str, max_chars: int = 500) -> List[str]:
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(len(text), start + max_chars)
        chunks.append(text[start:end])
        start = end
    return chunks


def build_embeddings_for_products(limit: int = 1000):
    db = SessionLocal()
    try:
        products = db.query(models.Product).limit(limit).all()
        to_insert = []
        texts = []
        meta = []
        for p in products:
            combined = "\n".join(filter(None, [p.title, p.category or "", str(p.features) if p.features else "", p.description or ""]))
            chunks = chunk_text(combined, max_chars=700)
            for c in chunks:
                texts.append(c)
                meta.append({"product_id": p.id, "title": p.title, "source_url": p.source_url})

        if not texts:
            return 0

        embeddings = embed_texts(texts)

        for emb, m, txt in zip(embeddings, meta, texts):
            obj = models.ProductChunk(product_id=m["product_id"], chunk_text=txt, embedding=emb, meta=m)
            db.add(obj)
        db.commit()
        return len(embeddings)
    finally:
        db.close()


def search_knn(query: str, top_k: int = 5) -> List[Tuple[int, float, str]]:
    """Return list of tuples (product_id, score, chunk_text) ordered by descending score"""
    db = SessionLocal()
    try:
        model = get_embedding_model()
        q_emb = model.encode([query], convert_to_numpy=True)[0]

        rows = db.query(models.ProductChunk).all()
        if not rows:
            return []
        embs = []
        metas = []
        texts = []
        prod_ids = []
        for r in rows:
            if not r.embedding:
                continue
            embs.append(np.array(r.embedding, dtype=np.float32))
            metas.append(r.meta)
            texts.append(r.chunk_text)
            prod_ids.append(r.product_id)

        embs = np.vstack(embs)
        q = q_emb.astype(np.float32)
        # cosine similarity
        embs_norm = embs / np.linalg.norm(embs, axis=1, keepdims=True)
        q_norm = q / np.linalg.norm(q)
        sims = (embs_norm @ q_norm)
        idx = np.argsort(-sims)[:top_k]
        results = []
        for i in idx:
            results.append((prod_ids[i], float(sims[i]), texts[i]))
        return results
    finally:
        db.close()
