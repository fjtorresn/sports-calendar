from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.app.core.database import get_db
from src.app.models.sports import Sport, Nation
from src.app.schemas.sports import SportResponse, NationResponse
from src.app.models.event import *
from src.app.models.user import *

router = APIRouter()

@router.get("/sports", response_model=List[SportResponse])
def get_sports(db: Session = Depends(get_db)):
    sports = db.query(Sport).all()
    return sports

@router.get("/nations", response_model=List[NationResponse])
def get_nations(db: Session = Depends(get_db)):
    nations = db.query(Nation).all()
    return nations