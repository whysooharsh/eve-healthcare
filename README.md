# EVE Diagnostics

Backend for diagnostic test bookings with simulated payments.

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

With Postgres:

```bash
docker compose up --build
```

Env: `DATABASE_URL` (default `sqlite:///./app.db`), `JWT_SECRET`, `JWT_EXPIRE_MINUTES`, `REDIS_URL` (optional, e.g. `redis://localhost:6379/0`).
Docs: `GET /docs`.

Redis caches `GET /centres/` and `GET /tests/` for 60s, invalidated on writes; app runs fine without it.

## Endpoints

```bash
POST /auth/signup {"email","password"}
POST /auth/login -> {"access_token"}
POST /centres/ {"name","location"} (auth)
GET /centres/?limit=20&offset=0
GET /centres/{id}
POST /tests/ {"centre_id","name","price"} (auth)
GET /tests/?centre_id=&limit=&offset=
POST /bookings/ {"test_id","appointment_at"} (auth, future date, amount copied from test, PENDING)
GET /bookings/?limit=&offset= (own only)
GET /bookings/{id} (own only)
POST /bookings/{id}/cancel (own PENDING only)
POST /payments/ {"booking_id","succeed":true} (auth, own PENDING/FAILED only)
POST /payments/webhook/ {"event_id","booking_id","status":"SUCCESS|FAILED"} (no auth, idempotent)
GET /health
```

Auth: `Authorization: Bearer <token>`.

## Schema

`users(id, email unique, password_hash)` → `bookings(user_id, test_id, centre_id, appointment_at, amount, status PENDING|CONFIRMED|FAILED|CANCELLED)`; `centres(id, name, location)` → `tests(centre_id, name, price)`; `payments(id, booking_id unique, amount, status, provider_event_id unique)`. Amount is snapshotted from the test at booking time so later price changes never rewrite history. Webhook idempotency keys on `payments.provider_event_id`: a repeat `event_id` returns the stored payment without touching the booking.

## Assumptions

SQLite by default, Postgres via `DATABASE_URL`. Tables auto-created on startup, no migrations. Webhook is unauthenticated by design (simulated provider) and never flips a `CANCELLED` booking. One payment row per booking, retried in place. `succeed` flag on `POST /payments/` is the simulator stand-in for a gateway.

## With more time

Alembic migrations, webhook signature secret + retries, refresh tokens, RBAC admin role for centres, rate limiting, structured logging.
