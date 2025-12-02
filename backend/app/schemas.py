from typing import Optional, List, Any
from pydantic import BaseModel, Field


class ProductBase(BaseModel):
    title: str
    price: Optional[str] = None
    description: Optional[str] = None
    features: Optional[Any] = None
    image_url: Optional[str] = None
    category: Optional[str] = None
    source_url: Optional[str] = None


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int

    class Config:
        orm_mode = True


class ChunkCreate(BaseModel):
    product_id: int
    chunk_text: str
    embedding: Optional[List[float]] = None
    meta: Optional[Any] = None
