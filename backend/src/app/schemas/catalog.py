from pydantic import BaseModel, ConfigDict

from app.models.enums import CompetitorKind


class ORMModel(BaseModel):
    # Allow building schemas straight from SQLAlchemy objects.
    model_config = ConfigDict(from_attributes=True)


class NationResponse(ORMModel):
    id: int
    name: str
    code: str


class EventKindResponse(ORMModel):
    id: int
    slug: str
    name: str
    is_default: bool


class SportResponse(ORMModel):
    id: int
    slug: str
    name: str


class CompetitionResponse(ORMModel):
    id: int
    sport_id: int
    slug: str
    name: str


class CompetitorResponse(ORMModel):
    id: int
    sport_id: int
    kind: CompetitorKind
    name: str
    short_name: str | None
