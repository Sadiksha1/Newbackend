from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models, schemas

router = APIRouter(prefix="/payment", tags=["Payment"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# -----------------------------
# 1. Create a new order
# -----------------------------
@router.post("/create-order", response_model=schemas.OrderOut)
async def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == order.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    total_amount = round(product.price * order.quantity, 2)

    new_order = models.Order(
        amount=total_amount,
        product_id=product.id,
        quantity=order.quantity,
        status="pending",
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    return new_order

# -----------------------------
# 2. Fonepay scans → user mobile opens this link
# -----------------------------
@router.get("/scan/{order_id}")
async def scan_payment(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "paid":
        return {"message": "Payment already processed. You may return to the machine."}

    order.status = "paid"
    db.commit()

    return {"message": "Payment successful! You may return to the machine."}

# -----------------------------
# 3. Checkout page polls this
# -----------------------------
@router.get("/status/{order_id}")
async def check_status(order_id: int, db: Session = Depends(get_db)):

    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return {"status": order.status}
