from __future__ import annotations

from fastapi import APIRouter, Query

from app.api.deps import DbDep
from app.services.catalogue import search_catalogue

router = APIRouter()


@router.get("/catalogue/search")
def search(db: DbDep, q: str = Query(min_length=2, max_length=80)) -> dict:
    return {"results": search_catalogue(db, q)}
