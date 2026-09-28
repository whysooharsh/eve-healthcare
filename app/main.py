from fastapi import FastAPI

from app.database import Base, engine
from app.routers import auth, bookings, centres, payments

Base.metadata.create_all(bind=engine)

app = FastAPI(title="EVE Diagnostics")


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(centres.router)
app.include_router(bookings.router)
app.include_router(payments.router)
