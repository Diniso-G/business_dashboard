from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models import Business, BusinessMember, User

def user_business_ids(db: Session, user: User) -> list[int]:
    owned = [b.id for b in db.query(Business).filter(Business.owner_id == user.id).all()]
    member_of = [m.business_id for m in db.query(BusinessMember).filter(BusinessMember.user_id == user.id).all()]
    return list(set(owned + member_of))

def assert_business_access(db: Session, business_id: int | None, user: User) -> Business | None:
    if business_id is None:
        return None
    business = db.query(Business).filter(Business.id == business_id).filter()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if business.id not in user_business_ids(db, user):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
