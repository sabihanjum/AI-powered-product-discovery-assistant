"""Script to create embeddings for products and store chunks in product_chunks table."""
from app.retrieval import build_embeddings_for_products


def main():
    n = build_embeddings_for_products()
    print(f"Created {n} embeddings/chunks")


if __name__ == "__main__":
    main()
