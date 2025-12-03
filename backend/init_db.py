"""Startup script to initialize database with products."""
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base, SessionLocal
from app import models, crud, schemas
from scraper.scraper import scrape_site

def init_db():
    """Create tables and seed with products if empty."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # Check if we have products
        count = db.query(models.Product).count()
        print(f"Current product count: {count}")
        
        if count == 0:
            print("No products found. Scraping traya.health...")
            try:
                products = scrape_site("traya")
                inserted = 0
                for p in products:
                    try:
                        prod_in = schemas.ProductCreate(**p)
                        crud.create_product(db, prod_in)
                        inserted += 1
                    except Exception as e:
                        print(f"Skipping product: {e}")
                        continue
                print(f"Inserted {inserted} products")
                
                # Create simple chunks for search
                print("Creating search chunks...")
                products = db.query(models.Product).all()
                for p in products:
                    text = f"{p.title} {p.category or ''} {p.description or ''}"
                    chunk = models.ProductChunk(
                        product_id=p.id,
                        chunk_text=text[:700],
                        embedding=[],  # Empty for simple search
                        meta={"product_id": p.id, "title": p.title}
                    )
                    db.add(chunk)
                db.commit()
                print(f"Created {len(products)} search chunks")
                
            except Exception as e:
                print(f"Scraping failed: {e}")
        else:
            print("Products already exist, skipping seed.")
            
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
    print("Database initialized!")
