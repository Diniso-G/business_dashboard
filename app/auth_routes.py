#route for user and authorization

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

import re
from app.database import get_db
from app.models import User
from app.auth import hash_password, verify_password, create_access_token

router = APIRouter()

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

def _validate_email(v: str) -> str:
    if not EMAIL_RE.match(v):
        raise ValueError("invalid email format")
    return v

class RegisterRequest(BaseModel):
    email: str
    password: str = Field(min_length=4)

    _validate_email = field_validator("email")(_validate_email)

class LoginRequest(BaseModel):
    email: str
    password: str = Field(min_length=4)

    _validate_email = field_validator("email")(_validate_email)

@router.post("/register")
def register(payload: RegisterRequest, db:Session = Depends(get_db)):
    existing = db.query(User).filter(User.email==payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=payload.email, hashed_password=hash_password(payload.password),)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
def login(payload: LoginRequest, db:Session = Depends(get_db)):
    user = db.query(User).filter(User.email==payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": user.email})
    return {"access_token": token, "token_type": "bearer"}


