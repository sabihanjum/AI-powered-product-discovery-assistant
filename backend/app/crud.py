from sqlalchemy.orm import Session
from . import models, schemas


def create_product(db: Session, product_in: schemas.ProductCreate):
    obj = models.Product(
        title=product_in.title,
        price=product_in.price,
        description=product_in.description,
        features=product_in.features,
        image_url=product_in.image_url,
        category=product_in.category,
        source_url=product_in.source_url,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_product(db: Session, product_id: int):
    return db.query(models.Product).filter(models.Product.id == product_id).first()


def list_products(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Product).offset(skip).limit(limit).all()
