from pydantic import BaseModel, ConfigDict
from typing import Optional

# ==========================================
# NATION SCHEMAS
# ==========================================
class NationBase(BaseModel):
    name: str
    iso_code: str
    flag_url: Optional[str] = None

# Usado para crear una nueva nación (POST)
class NationCreate(NationBase):
    pass

# Usado para devolver la nación al frontend (GET)
class NationResponse(NationBase):
    id: int
    
    # Esto le dice a Pydantic: "Lee el objeto de SQLAlchemy y conviértelo a JSON"
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