from __future__ import annotations

from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.orm import Session

from backend.app.db import Base, engine, get_db
from backend.app.models import Production, ProductionFormat

app = FastAPI(title="YouTube News Automation", version="0.1.0")


@app.on_event("startup")
def _startup():
    # MVP: cria tabelas automaticamente. Em produção, use migrations (Alembic).
    Base.metadata.create_all(bind=engine)


@app.get("/health")
def health(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {"ok": True}


@app.post("/productions")
def create_production(
    format: ProductionFormat,
    rules: dict | None = None,
    event_id: int | None = None,
    db: Session = Depends(get_db),
):
    prod = Production(format=format, rules_json=rules or {}, event_id=event_id)
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return {"id": prod.id, "format": prod.format, "status": prod.status}

