from typing import List, Dict, Any, Tuple
import numpy as np
import os
from .database import SessionLocal
from . import models

_EMBED_MODEL = None
_USE_PRECOMPUTED = os.getenv("USE_PRECOMPUTED_EMBEDDINGS", "false").lower() == "true"


def get_embedding_model(name: str = "all-MiniLM-L6-v2"):
    """Load embedding model - with fallback for pre-computed mode"""
    global _EMBED_MODEL
    if _EMBED_MODEL is None:
        if _USE_PRECOMPUTED:
            # In precomputed mode, we use TF-IDF style matching for queries
            _EMBED_MODEL = "precomputed"
            print("Using pre-computed embeddings mode (lightweight)")
        else:
            try:
                from sentence_transformers import SentenceTransformer
                _EMBED_MODEL = SentenceTransformer(name)
                print("Loaded SentenceTransformer model")
            except Exception as e:
                print(f"Failed to load SentenceTransformer: {e}, using precomputed mode")
                _EMBED_MODEL = "precomputed"
    return _EMBED_MODEL


def enhanced_text_similarity(query: str, text: str) -> float:
    """
    Enhanced keyword-based similarity with TF-IDF-like scoring.
    Used when we have pre-computed embeddings but can't run the model for queries.
    """
    import re
    
    # Tokenize and normalize
    def tokenize(s):
        return set(re.findall(r'\b\w+\b', s.lower()))
    
    query_words = tokenize(query)
    text_words = tokenize(text)
    
    if not query_words or not text_words:
        return 0.0
    
    # Calculate weighted intersection
    intersection = query_words & text_words
    
    # Boost for important words (longer words often more meaningful)
    score = 0.0
    for word in intersection:
        word_weight = min(len(word) / 5.0, 2.0)  # Longer words get more weight
        score += word_weight
    
    # Normalize by query length
    max_possible = sum(min(len(w) / 5.0, 2.0) for w in query_words)
    if max_possible == 0:
        return 0.0
    
    return score / max_possible


def embed_texts(texts: List[str]) -> List[List[float]]:
    model = get_embedding_model()
    if model == "precomputed":
        # Return dummy embeddings - real embeddings should already be in DB
        return [[0.0] * 384 for _ in texts]
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
        
        rows = db.query(models.ProductChunk).all()
        if not rows:
            return []
        
        # Pre-computed mode: use enhanced text similarity on pre-computed chunk texts
        if model == "precomputed":
            results = []
            for r in rows:
                score = enhanced_text_similarity(query, r.chunk_text or "")
                if score > 0:
                    results.append((r.product_id, score, r.chunk_text))
            
            # If no keyword matches, return top results anyway based on title match
            if not results:
                for r in rows:
                    meta = r.meta or {}
                    title = meta.get("title", "") if isinstance(meta, dict) else ""
                    score = enhanced_text_similarity(query, title)
                    if score > 0:
                        results.append((r.product_id, score, r.chunk_text))
            
            results.sort(key=lambda x: x[1], reverse=True)
            return results[:top_k]
        
        # Full semantic search mode (with SentenceTransformer)
        q_emb = model.encode([query], convert_to_numpy=True)[0]
        
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

        if not embs:
            return []
            
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
