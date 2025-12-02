from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from .database import get_db, engine, Base
from . import crud, schemas, models
from scraper.scraper import scrape_site
from .retrieval import search_knn, build_embeddings_for_products, get_embedding_model
from .database import SessionLocal
from .llm import generate_response
from pydantic import BaseModel, Field
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.on_event("startup")
def on_startup():
    # create tables if they do not exist (for quick start)
    Base.metadata.create_all(bind=engine)


@router.post("/scrape")
def run_scraper(site: str = "furlenco", db: Session = Depends(get_db)):
    """Run scraper for a given site. Returns number of items inserted."""
    try:
        products = scrape_site(site)
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        raise HTTPException(status_code=500, detail=f"Scraping failed: {str(e)}")
    
    inserted = 0
    for p in products:
        try:
            prod_in = schemas.ProductCreate(**p)
            crud.create_product(db, prod_in)
            inserted += 1
        except Exception as e:
            logger.warning(f"Failed to insert product: {e}")
            continue
    return {"inserted": inserted, "attempted": len(products), "site": site}


@router.get("/products")
def products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max products to return"),
    search: Optional[str] = Query(None, description="Search in title/description"),
    category: Optional[str] = Query(None, description="Filter by category"),
    db: Session = Depends(get_db)
):
    """List products with optional filtering and pagination."""
    items = crud.list_products(db, skip=skip, limit=limit)
    
    # Apply filters if provided
    if search:
        search_lower = search.lower()
        items = [p for p in items if search_lower in (p.title or "").lower() or search_lower in (p.description or "").lower()]
    
    if category:
        items = [p for p in items if category.lower() in (p.category or "").lower()]
    
    return {
        "products": items,
        "count": len(items),
        "skip": skip,
        "limit": limit
    }


@router.get("/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a specific product."""
    item = crud.get_product(db, product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return item


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=2, max_length=1000, description="User's query")
    top_k: int = Field(3, ge=1, le=10, description="Number of recommendations")


class ProductRecommendation(BaseModel):
    product_id: int
    title: str
    score: float
    reason: str


class ChatResponse(BaseModel):
    message: str
    recommendations: List[ProductRecommendation]
    query: str


@router.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    """
    AI-powered product recommendation chat.
    
    Uses semantic search (embeddings) to find relevant products,
    then generates a natural language response using Gemini LLM.
    
    Edge cases handled:
    - Empty/short queries
    - No matching products
    - LLM failures (graceful fallback)
    """
    # Edge case: validate input
    query = req.message.strip()
    if len(query) < 2:
        return ChatResponse(
            message="Please provide a more detailed question about products you're looking for.",
            recommendations=[],
            query=query
        )
    
    # Ensure embedding model is loaded
    try:
        get_embedding_model()
    except Exception as e:
        logger.error(f"Embedding model error: {e}")
        raise HTTPException(status_code=503, detail="AI service temporarily unavailable")
    
    # Semantic search
    results = search_knn(query, top_k=10)
    
    # Edge case: no results found
    if not results:
        return ChatResponse(
            message="I couldn't find products matching your query. Try describing your needs differently, for example: 'I need help with hair fall' or 'looking for scalp treatment'.",
            recommendations=[],
            query=query
        )

    # Aggregate scores by product
    agg = {}
    context_snippets = []
    for prod_id, score, chunk in results:
        agg.setdefault(prod_id, {"score": 0.0, "chunks": []})
        agg[prod_id]["score"] += score
        agg[prod_id]["chunks"].append(chunk)
        context_snippets.append(chunk)

    # Pick top products
    ranked = sorted(agg.items(), key=lambda kv: kv[1]["score"], reverse=True)[:req.top_k]
    recs = []
    db = SessionLocal()
    try:
        for prod_id, info in ranked:
            prod = crud.get_product(db, prod_id)
            title = prod.title if prod else f"Product {prod_id}"
            reason = info["chunks"][0][:200] if info["chunks"] else "Matches your query"
            recs.append(ProductRecommendation(
                product_id=prod_id,
                title=title,
                score=round(info["score"], 3),
                reason=reason
            ))
    finally:
        db.close()

    # Build prompt for Gemini
    product_context = "\n".join([f"- {r.title}: {r.reason}" for r in recs])
    prompt = f"""You are a helpful product recommendation assistant for a health & wellness store.

Based on the user's query and these matching products, provide a friendly, helpful response.
Be concise (2-3 sentences) and explain WHY these products might help.

User Query: {query}

Matching Products:
{product_context}

Respond naturally as a helpful assistant. Don't use markdown or bullet points."""

    # Generate LLM response with fallback
    try:
        llm_out = generate_response(prompt)
    except Exception as e:
        logger.warning(f"LLM error: {e}")
        llm_out = None

    # Fallback message if LLM fails
    if not llm_out:
        product_names = ", ".join([r.title for r in recs[:2]])
        llm_out = f"Based on your query about '{query}', I recommend checking out {product_names}. These products are highly relevant to your needs."

    return ChatResponse(
        message=llm_out,
        recommendations=[r.dict() for r in recs],
        query=query
    )
