from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

from schemas.rituals.ritual_models import RitualRequest, RitualResponse
from services.rituals import ritual_generator as service
from services.rituals import ritual_repository as repo

router = APIRouter()


router = APIRouter()

@router.post("/daily", response_model=RitualResponse)
async def get_or_generate_ritual(request: RitualRequest):
    today_date = datetime.now().strftime("%Y-%m-%d")
    
    # 1. Check Cache
    cached = repo.fetch_cached_ritual(request.user_id, today_date)
    if cached:
        return {
            "status": "already_generated",
            "date": today_date,
            "data": {
                "calculated_raasi": cached['calculated_raasi'],
                "rituals": cached['ritual_json'],
                "parikaram": cached['parikaram']
            }
        }

    # 2. Generate
    try:
        new_plan = service.generate_ai_ritual(
            request.name, request.dob, request.tob, 
            request.city, request.state, today_date, request.lang
        )
        # 3. Save
        repo.save_new_ritual(request.user_id, today_date, request.lang, new_plan)
        
        return {"status": "newly_generated", "date": today_date, "data": new_plan}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@router.get("/history/{user_id}/{date}")
async def get_ritual_history(user_id: int, date: str):
    row = repo.fetch_history(user_id, date)
    if not row:
        raise HTTPException(status_code=404, detail="No history found")
    
    return {
        "user_id": user_id,
        "date": str(row['ritual_date']),
        "data": {
            "calculated_raasi": row['calculated_raasi'],
            "rituals": row['ritual_json'],
            "parikaram": row['parikaram']
        }
    }
