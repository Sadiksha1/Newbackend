from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas

router = APIRouter(prefix="/products", tags=["Products"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# GET all products
@router.get("/", response_model=list[schemas.ProductOut])
def get_all_products(db: Session = Depends(get_db)):
    return db.query(models.Product).all()

# POST - create a product
@router.post("/", response_model=schemas.ProductOut)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    new_product = models.Product(**product.dict())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

# PUT - update a product
@router.put("/{product_id}", response_model=schemas.ProductOut)
def update_product(product_id: int, updated_product: schemas.ProductCreate, db: Session = Depends(get_db)):
    product_db = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    for key, value in updated_product.dict().items():
        setattr(product_db, key, value)
    
    db.commit()
    db.refresh(product_db)
    return product_db

# DELETE - remove a product
@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product_db = db.query(models.Product).filter(models.Product.id == product_id).first()
    if not product_db:
        raise HTTPException(status_code=404, detail="Product not found")
    
    db.delete(product_db)
    db.commit()
    return {"message": "Product deleted successfully"}
