import os
import json
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import date, timedelta, datetime

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session
import re
import hashlib

from .database import get_db, User, Group, OnDemandRequest, health_check

# Initialize FastAPI app
app = FastAPI(title="Carpool API", version="0.1.0")

# Configure CORS for local dev and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://carpool-web-dzxkfcfuiq-uc.a.run.app",
        "https://carpool-web-37218666122.us-central1.run.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Constants
WEEKDAY_NAME_TO_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
    "Saturday": 5,
    "Sunday": 6,
}

email_re = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or os.environ.get("CARPOOL_AUTH_SALT", "carpool-salt")
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()

# Pydantic Models
class Profile(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[Dict[str, Optional[str]]] = None

class SignupIn(BaseModel):
    email: str
    password: str
    profile: Optional[Profile] = None

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if not email_re.match(v):
            raise ValueError("invalid email format")
        return v

    @field_validator("password")
    @classmethod
    def password_valid(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("must be at least 8 characters")
        if not re.search(r"[A-Z]", v):
            raise ValueError("must include at least one uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("must include at least one lowercase letter")
        if not re.search(r"[0-9]", v):
            raise ValueError("must include at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("must include at least one special character")
        return v

class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        if not email_re.match(v):
            raise ValueError("invalid email format")
        return v

class MeOut(BaseModel):
    email: str
    profile: Optional[Profile] = None

class Member(BaseModel):
    name: str
    email: Optional[str] = None

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        v = v.strip()
        return v or None

class GroupIn(BaseModel):
    name: str
    origin: str
    destination: str
    departure_time: str
    days: List[str]
    driver: str
    capacity: int
    members: List[Member]

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("members")
    @classmethod
    def members_valid(cls, v: List[Member]) -> List[Member]:
        if not v:
            raise ValueError("must have at least one member")
        return v

    @field_validator("days")
    @classmethod
    def days_valid(cls, v: List[str]) -> List[str]:
        allowed = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"}
        unique: List[str] = []
        for d in v:
            d = d.strip()
            if d not in unique:
                unique.append(d)
        if not unique:
            raise ValueError("must select at least one day")
        invalid = [d for d in unique if d not in allowed]
        if invalid:
            raise ValueError(f"invalid days: {invalid}; allowed: {sorted(allowed)}")
        return unique

class GroupOut(GroupIn):
    id: int

class OnDemandRequestIn(BaseModel):
    user_email: str
    origin: str
    destination: str
    date: str
    preferred_driver: Optional[str] = None

    @field_validator("origin", "destination")
    @classmethod
    def location_valid(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("location cannot be empty")
        return v

class OnDemandRequestOut(OnDemandRequestIn):
    id: int
    created_at: datetime

# Helper functions
def _normalize_members(raw_members) -> List[Member]:
    """Backfill legacy formats to Member objects."""
    normalized: List[Member] = []
    for m in raw_members:
        if isinstance(m, dict):
            name = m.get("name", "").strip()
            email = m.get("email", "").strip() or None
            if name:
                normalized.append(Member(name=name, email=email))
        elif isinstance(m, str):
            name = m.strip()
            if name:
                # Try to extract email if format is "Name <email>"
                email_match = re.search(r"<([^>]+)>", name)
                if email_match:
                    email = email_match.group(1)
                    name = name.replace(f"<{email}>", "").strip()
                    normalized.append(Member(name=name, email=email))
                else:
                    normalized.append(Member(name=name, email=None))
    return normalized

# API Routes
@app.get("/health")
async def health_endpoint() -> dict:
    db_healthy = health_check()
    return {"status": "ok", "database": "healthy" if db_healthy else "unhealthy"}

@app.get("/")
async def root() -> dict:
    return {"message": "Carpool API is running", "version": "0.1.0"}

@app.post("/auth/register", status_code=201, response_model=MeOut)
async def auth_register(payload: SignupIn, db: Session = Depends(get_db)) -> MeOut:
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="User already exists")
    
    # Hash password
    password_hash = _hash_password(payload.password)
    
    # Create new user
    user = User(email=payload.email, password_hash=password_hash)
    db.add(user)
    db.commit()
    db.refresh(user)
    
    return MeOut(email=user.email, profile=payload.profile)

@app.post("/auth/login", response_model=MeOut)
async def auth_login(payload: LoginIn, db: Session = Depends(get_db)) -> MeOut:
    # Find user
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # Verify password
    password_hash = _hash_password(payload.password)
    if user.password_hash != password_hash:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return MeOut(email=user.email, profile=None)

@app.get("/auth/me", response_model=MeOut)
async def auth_me(x_user_email: Optional[str] = Header(default=None, alias="X-User-Email"), db: Session = Depends(get_db)) -> MeOut:
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email header")
    
    user = db.query(User).filter(User.email == x_user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return MeOut(email=user.email, profile=None)

@app.get("/groups", response_model=List[GroupOut])
async def list_groups(db: Session = Depends(get_db)) -> List[GroupOut]:
    groups = db.query(Group).all()
    result: List[GroupOut] = []
    for group in groups:
        members = json.loads(group.members) if group.members else []
        days_of_week = json.loads(group.days_of_week) if group.days_of_week else []
        result.append(
            GroupOut(
                id=group.id,
                name=group.name,
                origin=group.origin,
                destination=group.destination,
                departure_time=group.departure_time,
                days=days_of_week,
                driver=group.driver,
                capacity=group.capacity,
                members=_normalize_members(members),
            )
        )
    return result

@app.get("/groups/{name}", response_model=GroupOut)
async def get_group(name: str, db: Session = Depends(get_db)) -> GroupOut:
    group = db.query(Group).filter(Group.name == name).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    members = json.loads(group.members) if group.members else []
    days_of_week = json.loads(group.days_of_week) if group.days_of_week else []
    
    return GroupOut(
        id=group.id,
        name=group.name,
        origin=group.origin,
        destination=group.destination,
        departure_time=group.departure_time,
        days=days_of_week,
        driver=group.driver,
        capacity=group.capacity,
        members=_normalize_members(members),
    )

@app.post("/groups", status_code=201, response_model=GroupOut)
async def create_group(group: GroupIn, db: Session = Depends(get_db)) -> GroupOut:
    # Check if group name already exists
    existing_group = db.query(Group).filter(Group.name == group.name).first()
    if existing_group:
        raise HTTPException(status_code=409, detail="Group name already exists")
    
    # Create new group
    members_json = json.dumps([m.model_dump() for m in group.members])
    days_json = json.dumps(group.days)
    
    new_group = Group(
        name=group.name,
        origin=group.origin,
        destination=group.destination,
        departure_time=group.departure_time,
        days_of_week=days_json,
        driver=group.driver,
        capacity=group.capacity,
        members=members_json
    )
    
    db.add(new_group)
    db.commit()
    db.refresh(new_group)
    
    return GroupOut(
        id=new_group.id,
        name=new_group.name,
        origin=new_group.origin,
        destination=new_group.destination,
        departure_time=new_group.departure_time,
        days=group.days,
        driver=new_group.driver,
        capacity=new_group.capacity,
        members=group.members,
    )

@app.delete("/groups/{name}", status_code=204)
async def delete_group(name: str, db: Session = Depends(get_db)):
    group = db.query(Group).filter(Group.name == name).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    db.delete(group)
    db.commit()
    return None

@app.post("/on-demand/requests")
async def create_on_demand_request(request: OnDemandRequestIn, db: Session = Depends(get_db)):
    """Create a new on-demand carpool request"""
    try:
        new_request = OnDemandRequest(
            user_email=request.user_email,
            origin=request.origin,
            destination=request.destination,
            date=request.date,
            preferred_driver=request.preferred_driver
        )
        
        db.add(new_request)
        db.commit()
        db.refresh(new_request)
        
        return {"message": "On-demand request created successfully", "request_id": new_request.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating request: {str(e)}")

@app.get("/on-demand/drivers")
async def get_available_drivers(db: Session = Depends(get_db)):
    """Get list of available drivers"""
    try:
        groups = db.query(Group).all()
        drivers = set()
        
        for group in groups:
            # Add the group driver
            drivers.add(group.driver)
            
            # Add members who could be drivers
            members = json.loads(group.members) if group.members else []
            for member in members:
                if isinstance(member, dict) and 'name' in member:
                    drivers.add(member['name'])
        
        return {"drivers": list(drivers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting drivers: {str(e)}")

@app.get("/on-demand/requests")
async def get_on_demand_requests(db: Session = Depends(get_db)):
    """Get all on-demand carpool requests"""
    try:
        requests = db.query(OnDemandRequest).all()
        return {"requests": [
            {
                "id": req.id,
                "user_email": req.user_email,
                "origin": req.origin,
                "destination": req.destination,
                "date": req.date,
                "preferred_driver": req.preferred_driver,
                "created_at": req.created_at
            }
            for req in requests
        ]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting requests: {str(e)}")

# Admin endpoints
@app.get("/admin/users")
async def list_users(db: Session = Depends(get_db)):
    """Get all users for admin purposes"""
    try:
        users = db.query(User).all()
        return {"users": [{"id": user.id, "email": user.email, "created_at": user.created_at} for user in users]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting users: {str(e)}")

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    """Delete a user by ID"""
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        db.delete(user)
        db.commit()
        return {"message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting user: {str(e)}")

@app.delete("/admin/test-users")
async def cleanup_test_users(db: Session = Depends(get_db)):
    """Delete all test users (emails containing 'test' or 'demo')"""
    try:
        test_users = db.query(User).filter(
            (User.email.contains('test')) | (User.email.contains('demo'))
        ).all()
        
        count = len(test_users)
        for user in test_users:
            db.delete(user)
        
        db.commit()
        return {"message": f"Deleted {count} test users"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error cleaning up test users: {str(e)}")
