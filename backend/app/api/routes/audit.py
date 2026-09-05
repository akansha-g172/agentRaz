from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.audit_service import get_session_audit


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get("/sessions/{session_id}")
def get_audit_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    result = get_session_audit(db, session_id)
    if not result.get("found"):
        raise HTTPException(status_code=404, detail="Session not found")
    return result
