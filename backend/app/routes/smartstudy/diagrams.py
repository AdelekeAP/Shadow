"""
Diagram Routes - AI-Powered Concept Diagram Generation
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.schemas.smartstudy import DiagramCreate, DiagramResponse
from app.utils.auth import get_current_user
from app.middleware.rate_limiter import limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/diagrams", tags=["SmartStudy"])


@router.post("/", response_model=DiagramResponse)
@limiter.limit("10/minute")
async def create_diagram(
    request: Request,
    diagram_data: DiagramCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an interactive concept diagram for a topic."""
    from app.services.diagram_generator import generate_diagram

    try:
        result = await generate_diagram(
            db=db,
            user_id=str(current_user.id),
            topic=diagram_data.topic,
            course_code=diagram_data.course_code,
            diagram_type=diagram_data.diagram_type,
            context_hint=diagram_data.context_hint,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Diagram generation failed: %s", e, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to generate diagram. Please try again.",
        )
