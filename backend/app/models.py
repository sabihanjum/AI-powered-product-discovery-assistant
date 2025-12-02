import os
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from .database import Base

try:
    # pgvector integration (only enable if explicitly requested via env var)
    from pgvector.sqlalchemy import Vector
    if os.getenv("PGVECTOR_EXTENSION", "false").lower() in ("1", "true", "yes"):
        VECTOR_TYPE = Vector(1536)
    else:
        VECTOR_TYPE = String
except Exception:
    VECTOR_TYPE = String  # fallback for environments without pgvector installed


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    price = Column(String, nullable=True)
    description = Column(Text, nullable=True)
    features = Column(JSON, nullable=True)
    image_url = Column(String, nullable=True)
    category = Column(String, nullable=True)
    source_url = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    chunks = relationship("ProductChunk", back_populates="product")


class ProductChunk(Base):
    __tablename__ = "product_chunks"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False)
    chunk_text = Column(Text, nullable=False)
    # store embedding as JSON list for portability (pgvector optional)
    embedding = Column(JSON, nullable=True)
    meta = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    product = relationship("Product", back_populates="chunks")
