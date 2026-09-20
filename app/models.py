from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, UniqueConstraint

from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base, engine, SessionLocal

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    reports = relationship("Report", back_populates="owner")
    owned_businesses = relationship("Business", back_populates="owner")
    membership = relationship("BusinessMember", back_populates="user")

class Business(Base):
    __tablename__ = "businesses"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    owner = relationship("User", back_populates="owned_businesses")
    members = relationship("BusinessMember", back_populates="business", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="business")

class BusinessMember(Base):
    __tablename__ = "business_members"
    id = Column(Integer, primary_key=True)
    business_id = Column(Integer, ForeignKey("businesses.id"))
    owner_id = Column(Integer, ForeignKey("users.id"))
    role = Column(String, default="member")
    invited_at = Column(DateTime, default=datetime.utcnow)
    
    business = relationship("Business", back_populates="member")
    user = relationship("User", back_populates="memberships")
    __table_args__ = (UniqueConstraint("business_id", "user_id", name="uq_business_user"),)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True)
    filename = Column(String)
    total_revenue = Column(Float)
    avg_order_value = Column(Float)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    business_id = Column(Integer, ForeignKey("business.id"), nullable=True)

    results_json = Column(Text)
    charts_json = Column(Text)
    ai_recommendations = Column(Text)

    owner = relationship("User", back_populates="reports")
    business = relationship("Business", back_populates="reports")

Base.metadata.create_all(engine)
