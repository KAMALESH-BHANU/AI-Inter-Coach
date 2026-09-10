from fastapi import APIRouter, Query
from typing import List, Dict, Optional
from app.services.question_service import TAXONOMY_SKILLS, CATEGORIZED_SKILLS

router = APIRouter(prefix="/api/questions", tags=["Questions & Skills Taxonomy"])

@router.get("/skills", response_model=List[str])
async def get_taxonomy_skills(search: Optional[str] = Query(None)):
    """
    Returns searchable list of technical skills for the manual skill selection UI.
    """
    if not search:
        return sorted(TAXONOMY_SKILLS)
    
    query = search.lower().strip()
    filtered = [s for s in TAXONOMY_SKILLS if query in s.lower()]
    return sorted(filtered)

@router.get("/skills/categories", response_model=Dict[str, List[str]])
async def get_categorized_skills():
    """
    Returns all skills organized by category (Languages, Frontend, Backend, Databases, Core CS, DevOps, AI).
    """
    return CATEGORIZED_SKILLS
