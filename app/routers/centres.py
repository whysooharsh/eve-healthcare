from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.database import get_db

router = APIRouter(tags=["centres"])


@router.post("/centres/", response_model=schemas.CentreOut, status_code=201)
def create_centre(body: schemas.CentreIn, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    centre = models.Centre(name=body.name, location=body.location)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    return centre


@router.get("/centres/", response_model=list[schemas.CentreOut])
def list_centres(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    return db.query(models.Centre).order_by(models.Centre.id).offset(offset).limit(limit).all()


@router.get("/centres/{centre_id}", response_model=schemas.CentreDetailOut)
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    centre = db.get(models.Centre, centre_id)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    return centre


@router.post("/tests/", response_model=schemas.TestOut, status_code=201)
def create_test(body: schemas.TestIn, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    if not db.get(models.Centre, body.centre_id):
        raise HTTPException(status_code=404, detail="Centre not found")
    test = models.DiagnosticTest(centre_id=body.centre_id, name=body.name, price=body.price)
    db.add(test)
    db.commit()
    db.refresh(test)
    return test


@router.get("/tests/", response_model=list[schemas.TestOut])
def list_tests(
    centre_id: int | None = None,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    q = db.query(models.DiagnosticTest).order_by(models.DiagnosticTest.id)
    if centre_id is not None:
        q = q.filter_by(centre_id=centre_id)
    return q.offset(offset).limit(limit).all()
