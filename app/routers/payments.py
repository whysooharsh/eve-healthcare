from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.models import BookingStatus, PaymentStatus

router = APIRouter(tags=["payments"])


def apply_result(booking: models.Booking, payment: models.Payment, success: bool) -> None:
    if booking.status == BookingStatus.CANCELLED.value:
        return
    if success:
        payment.status = PaymentStatus.SUCCESS.value
        booking.status = BookingStatus.CONFIRMED.value
    else:
        payment.status = PaymentStatus.FAILED.value
        booking.status = BookingStatus.FAILED.value


@router.post("/payments/", response_model=schemas.PaymentOut, status_code=201)
def pay(body: schemas.PaymentIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    booking = db.get(models.Booking, body.booking_id)
    if not booking or booking.user_id != user.id:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in (BookingStatus.PENDING.value, BookingStatus.FAILED.value):
        raise HTTPException(status_code=400, detail="Booking cannot be paid in its current status")
    payment = db.query(models.Payment).filter_by(booking_id=booking.id).first()
    if not payment:
        payment = models.Payment(booking_id=booking.id, amount=booking.amount, status=PaymentStatus.PENDING.value)
        db.add(payment)
        db.flush()
    apply_result(booking, payment, body.succeed)
    db.commit()
    db.refresh(payment)
    return payment


@router.post("/payments/webhook/", response_model=schemas.PaymentOut)
def webhook(body: schemas.WebhookIn, db: Session = Depends(get_db)):
    seen = db.query(models.Payment).filter_by(provider_event_id=body.event_id).first()
    if seen:
        return seen
    booking = db.get(models.Booking, body.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    payment = db.query(models.Payment).filter_by(booking_id=booking.id).first()
    if not payment:
        payment = models.Payment(booking_id=booking.id, amount=booking.amount, status=PaymentStatus.PENDING.value)
        db.add(payment)
        db.flush()
    payment.provider_event_id = body.event_id
    apply_result(booking, payment, body.status == PaymentStatus.SUCCESS.value)
    db.commit()
    db.refresh(payment)
    return payment
