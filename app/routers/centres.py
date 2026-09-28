from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_current_user
from app.cache import get_json, invalidate, set_json
from app.database import get_db

router = APIRouter(tags=["centres"])


@router.post("/centres/", response_model=schemas.CentreOut, status_code=201)
def create_centre(body: schemas.CentreIn, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    centre = models.Centre(name=body.name, location=body.location)
    db.add(centre)
    db.commit()
    db.refresh(centre)
    invalidate("centres:")
    return centre


@router.get("/centres/", response_model=list[schemas.CentreOut])
def list_centres(limit: int = Query(20, ge=1, le=100), offset: int = Query(0, ge=0), db: Session = Depends(get_db)):
    key = f"centres:list:{limit}:{offset}"
    cached = get_json(key)
    if cached is not None:
        return cached
    rows = db.query(models.Centre).order_by(models.Centre.id).offset(offset).limit(limit).all()
    out = [schemas.CentreOut.model_validate(r).model_dump() for r in rows]
    set_json(key, out)
    return out


@router.get("/centres/{centre_id}", response_model=schemas.CentreDetailOut)
def get_centre(centre_id: int, db: Session = Depends(get_db)):
    key = f"centres:detail:{centre_id}"
    cached = get_json(key)
    if cached is not None:
        return cached
    centre = db.get(models.Centre, centre_id)
    if not centre:
        raise HTTPException(status_code=404, detail="Centre not found")
    out = schemas.CentreDetailOut.model_validate(centre).model_dump()
    set_json(key, out)
    return out


@router.post("/tests/", response_model=schemas.TestOut, status_code=201)
def create_test(body: schemas.TestIn, db: Session = Depends(get_db), _: models.User = Depends(get_current_user)):
    if not db.get(models.Centre, body.centre_id):
        raise HTTPException(status_code=404, detail="Centre not found")
    test = models.DiagnosticTest(centre_id=body.centre_id, name=body.name, price=body.price)
    db.add(test)
    db.commit()
    db.refresh(test)
    invalidate("tests:", "centres:")
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
    key = f"tests:list:{centre_id}:{limit}:{offset}"
    cached = get_json(key)
    if cached is not None:
        return cached
    rows = q.offset(offset).limit(limit).all()
    out = [schemas.TestOut.model_validate(r).model_dump() for r in rows]
    set_json(key, out)
    return out
