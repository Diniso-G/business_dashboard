from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Business, BusinessMember, User
from app.auth import get_current_user
from app.access import user_business_ids, assert_business_access

router = APIRouter(prefix="/businesses", tags=["businesses"])

class BusinessCreate(BaseModel):
    name: str

class InviteRequest(BaseModel):
    email: EmailStr

def _user_business_ids(db:Session, user: User) -> list[int]:
    return user_business_ids(db, user)
    ''''
    owned = [b.id for b in db.query(Business).filter(Business.owner_id == user.id).all()]
    member_of = [m.business_id for m in db.query(BusinessMember).filter(BusinessMember.user_id == user.id).all()]
    return list(set(owned + member_of))
    '''

def _assert_access(db:Session, business_id: int, user:User) -> Business:
    return assert_business_access(db, business_id, user)
    ''''
    business = db.query(Business).filter(Business.id == business_id).first()
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")
    if business.id not in _user_business_ids(db, user):
        raise HTTPException(status_code=403, detail="You don't have access to this business")
    return business
'''
    
@router.post("")
def create_business(payload: BusinessCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    business = Business(name=payload.name.strip(), owner_id=user.id)
    db.add(business)
    db.commit()
    db.refresh(business)

    member = BusinessMember(business_id=business.id, user_id=user.id, role="owner")
    db.add(member)
    db.commit()

    return {"id": business.id, "name": business.name}

@router.get("")
def list_businesses(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    ids = _user_business_ids(db, user)
    businesses = db.query(Business).filter(Business.id.in_(ids)).all() if ids else []
    return [
        {"id": b.id, "name": b.name, "is_owner": b.owner == user.id}
        for b in businesses
    ]

@router.get("/{business_id}/members")
def list_members(business_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _assert_access(db, business_id, user)
    members = db.query(BusinessMember).filter(BusinessMember.business_id == business_id).all()
    return [
        {"email": m.user.email, "role": m.role, "invited_at": m.invited_at.isoformat()}
        for m in members
    ]

@router.post("/{business_id}/invite")
def invite_member(business_id: int, payload: InviteRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    business = _assert_access(db, business_id, user)
    if business.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Only the owner can invite teammates")
    invitee = db.query(User).filter(User.email == payload.email).first()
    if not invitee:
        raise HTTPException(status_code=404, detail="No registered user with that email yet- they need to register first")

    existing = db.query(BusinessMember).filter(BusinessMember.business_id == business_id, BusinessMember.user_id == invitee.id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Already a member")

    member = BusinessMember(business_id=business_id, user_id=invitee.id, role="member")
    db.add(member)
    db.commit()
    return {"member": f"{payload.email} added to {business.name}"}

