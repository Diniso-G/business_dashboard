from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.email_utils import send_all_digests
from app.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/send-digests")
def trigger_digests(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    return send_all_digests(db)
