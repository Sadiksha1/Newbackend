from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import SessionLocal
from .. import models, schemas
from ..utils.qr import generate_fonepay_qr
import uuid
import os

router = APIRouter(prefix="/payment", tags=["Payment"])

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/create", response_model=schemas.PaymentOut)
def create_payment(payload: schemas.PaymentCreate, db: Session = Depends(get_db)):
    # create payment id
    payment_id = str(uuid.uuid4())

    # Validate product/order existence if IDs provided
    if payload.product_id:
        product = db.query(models.Product).filter(models.Product.id == payload.product_id).first()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
    if payload.order_id:
        order = db.query(models.Order).filter(models.Order.id == payload.order_id).first()
        if not order:
            raise HTTPException(status_code=404, detail="Order not found")

    invoice_number, filepath = generate_fonepay_qr(payload.amount, f"product_{payload.product_id or 'unknown'}")
    qr_filename = os.path.basename(filepath)

    payment = models.Payment(
        id=payment_id,
        order_id=payload.order_id,
        product_id=payload.product_id,
        amount=payload.amount,
        status="PENDING",
        qr_filename=qr_filename,
        invoice_number=invoice_number
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    return schemas.PaymentOut(
        id=payment.id,
        order_id=payment.order_id,
        product_id=payment.product_id,
        amount=payment.amount,
        status=payment.status,
        qr_code_url=f"/qrcodes/{qr_filename}",
        invoice_number=payment.invoice_number,
        created_at=payment.created_at
    )

@router.post("/verify/{payment_id}")
def verify_payment(payment_id: str, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Invalid payment ID")

    # Real-ready: here you would verify with the merchant/provider API.
    # For now we mark PAID and update linked order if exists.
    payment.status = "PAID"
    db.commit()

    if payment.order_id:
        order = db.query(models.Order).filter(models.Order.id == payment.order_id).first()
        if order:
            order.status = "PAID"
            db.commit()

    return {"message": "Payment verified (simulated) and order updated if linked."}

@router.get("/status/{payment_id}", response_model=schemas.PaymentStatusOut)
def check_status(payment_id: str, db: Session = Depends(get_db)):
    payment = db.query(models.Payment).filter(models.Payment.id == payment_id).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Invalid payment ID")
    return {"payment_id": payment.id, "status": payment.status}
