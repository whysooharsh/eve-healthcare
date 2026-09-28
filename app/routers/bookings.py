from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db
from app.models import BookingStatus

router = APIRouter(tags=["bookings"])


def owned_booking(db: Session, booking_id: int, user_id: int) -> models.Booking:
    booking = db.get(models.Booking, booking_id)
    if not booking or booking.user_id != user_id:
        raise HTTPException(status_code=404, detail="Booking not found")
    return booking


@router.post("/bookings/", response_model=schemas.BookingOut, status_code=201)
def create_booking(body: schemas.BookingIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    test = db.get(models.DiagnosticTest, body.test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")
    booking = models.Booking(
        user_id=user.id,
        test_id=test.id,
        centre_id=test.centre_id,
        appointment_at=body.appointment_at,
        amount=test.price,
        status=BookingStatus.PENDING.value,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)
    return booking


@router.get("/bookings/", response_model=list[schemas.BookingOut])
def list_bookings(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user),
):
    return (
        db.query(models.Booking)
        .filter_by(user_id=user.id)
        .order_by(models.Booking.id)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/bookings/{booking_id}", response_model=schemas.BookingOut)
def get_booking(booking_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    return owned_booking(db, booking_id, user.id)


@router.post("/bookings/{booking_id}/cancel", response_model=schemas.BookingOut)
def cancel_booking(booking_id: int, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    booking = owned_booking(db, booking_id, user.id)
    if booking.status != BookingStatus.PENDING.value:
        raise HTTPException(status_code=400, detail="Only PENDING bookings can be cancelled")
    booking.status = BookingStatus.CANCELLED.value
    db.commit()
    db.refresh(booking)
    return booking
