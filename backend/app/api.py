from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from .database import get_db, engine, Base
from . import crud, schemas, models
from scraper.scraper import scrape_site
from .retrieval import search_knn, build_embeddings_for_products, get_embedding_model
from .database import SessionLocal
from .llm import generate_response
from pydantic import BaseModel

router = APIRouter()


@router.on_event("startup")
def on_startup():
    # create tables if they do not exist (for quick start)
    Base.metadata.create_all(bind=engine)


@router.post("/scrape")
def run_scraper(site: str = "furlenco", db: Session = Depends(get_db)):
    """Run scraper for a given site (simple scaffold). Returns number of items inserted."""
    products = scrape_site(site)
    inserted = 0
    for p in products:
        try:
            prod_in = schemas.ProductCreate(**p)
            crud.create_product(db, prod_in)
            inserted += 1
        except Exception:
            # skip bad items, continue
            continue
    return {"inserted": inserted, "attempted": len(products)}


@router.get("/products")
def products(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    items = crud.list_products(db, skip=skip, limit=limit)
    return items


@router.get("/products/{product_id}")
def product_detail(product_id: int, db: Session = Depends(get_db)):
    item = crud.get_product(db, product_id)
    if not item:
        raise HTTPException(status_code=404, detail="Product not found")
    return item


class ChatRequest(BaseModel):
    message: str


@router.post("/chat")
def chat(req: ChatRequest):
    """Simple retrieval + template-based recommendation using local embeddings."""
    # ensure model is loaded
    get_embedding_model()
    results = search_knn(req.message, top_k=10)
    if not results:
        return {"message": "I couldn't find relevant products.", "recommendations": []}

    # aggregate scores by product
    agg = {}
    context_snippets = []
    for prod_id, score, chunk in results:
        agg.setdefault(prod_id, {"score": 0.0, "chunks": []})
        agg[prod_id]["score"] += score
        agg[prod_id]["chunks"].append(chunk)
        context_snippets.append(chunk)

    # pick top 3 products
    ranked = sorted(agg.items(), key=lambda kv: kv[1]["score"], reverse=True)[:3]
    recs = []
    db = SessionLocal()
    try:
        for prod_id, info in ranked:
            prod = crud.get_product(db, prod_id)
            title = prod.title if prod else f"Product {prod_id}"
            reason = info["chunks"][0][:200]
            recs.append({"product_id": prod_id, "title": title, "score": info["score"], "reason": reason})
    finally:
        db.close()

    # Build a prompt for Gemini if available
    prompt = "You are a product recommendation assistant. Use the context and user's query to recommend up to 3 products with short explanations.\n"
    prompt += "Context snippets:\n" + "\n---\n".join(context_snippets[:6]) + "\n"
    prompt += f"User query: {req.message}\n"
    try:
        llm_out = generate_response(prompt)
    except Exception:
        llm_out = None

    message = llm_out or "I found some products you might like based on your query."
    return {"message": message, "recommendations": recs}
