from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
from ..utils.qr import generate_fonepay_qr
import uuid
import os

router = APIRouter(prefix="/checkout", tags=["Checkout"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create_order", response_model=schemas.OrderOut)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.id == order_in.product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    total = round(product.price * order_in.quantity, 2)
    order = models.Order(
        product_id=order_in.product_id,
        quantity=order_in.quantity,
        total_amount=total,
        status="PENDING"
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order

@router.post("/create_order_payment")
def create_order_payment(order_id: int, db: Session = Depends(get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status == "PAID":
        return {"message": "Order already paid"}

    payment_id = str(uuid.uuid4())
    invoice_number, filepath = generate_fonepay_qr(order.total_amount, f"order_{order.id}")
    qr_filename = os.path.basename(filepath)

    payment = models.Payment(
        id=payment_id,
        order_id=order.id,
        product_id=order.product_id,
        amount=order.total_amount,
        status="PENDING",
        qr_filename=qr_filename,
        invoice_number=invoice_number
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return {
        "payment_id": payment.id,
        "qr_code_url": f"/qrcodes/{qr_filename}",
        "invoice_number": invoice_number,
        "amount": payment.amount
    }