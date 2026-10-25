from pydantic import BaseModel, ConfigDict


# ==========================================
# NATION SCHEMAS
# ==========================================
class NationBase(BaseModel):
    name: str
    iso_code: str
    flag_url: str | None = None


class NationCreate(NationBase):
    pass


class NationResponse(NationBase):
    id: int

    # Allow building the schema from SQLAlchemy objects.
    model_config = ConfigDict(from_attributes=True)


# ==========================================
# SPORT SCHEMAS
# ==========================================
class SportBase(BaseModel):
    name: str
    participant_type: str


class SportCreate(SportBase):
    pass


class SportResponse(SportBase):
    id: int

    model_config = ConfigDict(from_attributes=True)
