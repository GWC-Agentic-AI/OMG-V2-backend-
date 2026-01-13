from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class RitualItem(BaseModel):
    id: str
    time: str
    title: str
    description: str

class ParikaramData(BaseModel):
    for_your_raasi: str
    specific_to_today: str

class RitualContent(BaseModel):
    calculated_raasi: str
    rituals: List[RitualItem]
    parikaram: ParikaramData

class RitualRequest(BaseModel):
    user_id: int
    name: str
    dob: str  # Format: YYYY-MM-DD
    tob: str  # Format: HH:MM
    city: str
    state: str
    lang: str # en, ta, hi, te, kn

class RitualResponse(BaseModel):
    status: str
    date: str
    data: RitualContent