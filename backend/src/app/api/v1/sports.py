from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sports import Nation, Sport
from app.schemas.sports import NationResponse, SportResponse

router = APIRouter()


@router.get("/sports", response_model=list[SportResponse])
def get_sports(db: Session = Depends(get_db)):
    sports = db.query(Sport).all()
    return sports


@router.get("/nations", response_model=list[NationResponse])
def get_nations(db: Session = Depends(get_db)):
    nations = db.query(Nation).all()
    return nations
