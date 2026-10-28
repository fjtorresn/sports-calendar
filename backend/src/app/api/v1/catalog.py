from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Competition, EventKind, Nation, Sport
from app.schemas.catalog import CompetitionResponse, EventKindResponse, NationResponse, SportResponse

router = APIRouter()


@router.get("/sports", response_model=list[SportResponse])
def list_sports(db: Session = Depends(get_db)) -> list[Sport]:
    return list(db.scalars(select(Sport).order_by(Sport.name)))


@router.get("/sports/{slug}/event-kinds", response_model=list[EventKindResponse])
def list_event_kinds(slug: str, db: Session = Depends(get_db)) -> list[EventKind]:
    sport = db.scalar(select(Sport).where(Sport.slug == slug))
    if sport is None:
        raise HTTPException(status_code=404, detail=f"Sport '{slug}' not found")
    return sport.event_kinds


@router.get("/sports/{slug}/competitions", response_model=list[CompetitionResponse])
def list_competitions(slug: str, db: Session = Depends(get_db)) -> list[Competition]:
    query = select(Competition).join(Sport).where(Sport.slug == slug).order_by(Competition.name)
    return list(db.scalars(query))


@router.get("/nations", response_model=list[NationResponse])
def list_nations(db: Session = Depends(get_db)) -> list[Nation]:
    return list(db.scalars(select(Nation).order_by(Nation.name)))
