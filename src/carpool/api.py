from pathlib import Path
from typing import List, Optional, Dict, Any

from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from tinydb import TinyDB, Query
from datetime import date, timedelta, datetime
import re
import hashlib
import os

# Initialize FastAPI app
app = FastAPI(title="Carpool API", version="0.1.0")

# Configure CORS for local dev and production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173", 
        "http://127.0.0.1:5173",
        "https://carpool-web-dzxkfcfuiq-uc.a.run.app",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# Resolve a data directory at the project root: <repo_root>/data/db.json
# File is located at src/carpool/api.py, so repo root is parents[2]
REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "db.json"

# Initialize TinyDB
_db = TinyDB(DB_PATH)
Groups = _db.table("groups")
OnDemand = _db.table("on_demand_requests")
Users = _db.table("users")
Q = Query()

WEEKDAY_NAME_TO_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}

email_re = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def _hash_password(password: str, salt: Optional[str] = None) -> str:
    salt = salt or os.environ.get("CARPOOL_AUTH_SALT", "carpool-salt")
    return hashlib.sha256((salt + password).encode("utf-8")).hexdigest()


class Profile(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    date_of_birth: Optional[str] = None  # ISO date string
    gender: Optional[str] = None
    address: Optional[Dict[str, Optional[str]]] = None  # {city,state,zip}


class SignupIn(BaseModel):
    email: str
    password: str
    profile: Optional[Profile] = None

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.strip()
        if not email_re.match(v):
            raise ValueError("invalid email format")
        return v

    @field_validator("password")
    @classmethod
    def password_rules(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("must be at least 8 characters")
        if not re.search(r"[A-Za-z]", v):
            raise ValueError("must include at least one letter")
        if not re.search(r"\d", v):
            raise ValueError("must include at least one number")
        if not re.search(r"[!@#$%^&*()_+\-=[\]{};':\"\\|,.<>/?]", v):
            raise ValueError("must include at least one special character")
        return v


class LoginIn(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_valid(cls, v: str) -> str:
        v = v.strip()
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
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("member name cannot be empty")
        return v

    @field_validator("email")
    @classmethod
    def email_clean(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        return v or None


class GroupIn(BaseModel):
    name: str
    members: List[Member]
    days: List[str]
    cycle_days: int

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("name cannot be empty")
        return v

    @field_validator("members")
    @classmethod
    def members_non_empty(cls, v: List[Member]) -> List[Member]:
        if not v:
            raise ValueError("members must have at least one value")
        return v

    @field_validator("days")
    @classmethod
    def days_valid(cls, v: List[str]) -> List[str]:
        allowed = {"Monday", "Tuesday", "Wednesday", "Thursday", "Friday"}
        unique: List[str] = []
        for d in v:
            d = d.strip()
            if d and d not in unique:
                unique.append(d)
        if not unique:
            raise ValueError("days must include at least one weekday")
        invalid = [d for d in unique if d not in allowed]
        if invalid:
            raise ValueError(f"invalid days: {invalid}; allowed: {sorted(allowed)}")
        return unique

    @field_validator("cycle_days")
    @classmethod
    def cycle_valid(cls, v: int) -> int:
        if v not in (10, 20, 30):
            raise ValueError("cycle_days must be one of 10, 20, 30")
        return v


class Group(GroupIn):
    id: int


class ScheduleRequest(BaseModel):
    start_date: date


class ScheduleItem(BaseModel):
    date: date
    driver: str


class StoredSchedule(BaseModel):
    start_date: date
    end_date: date
    items: List[ScheduleItem]


class OnDemandRequestIn(BaseModel):
    origin_lat: float
    origin_lng: float
    destination: str
    dest_lat: float
    dest_lng: float
    dest_place_id: Optional[str] = None
    dest_address: Optional[str] = None

    @field_validator("destination")
    @classmethod
    def dest_not_empty(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("destination cannot be empty")
        return v


class OnDemandRequest(OnDemandRequestIn):
    id: int
    created_at: datetime


@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}


def _normalize_members(raw_members) -> List[Member]:
    """Backfill legacy formats to Member objects."""
    normalized: List[Member] = []
    for m in raw_members or []:
        if isinstance(m, str):
            nm = m.strip()
            if nm:
                normalized.append(Member(name=nm))
        elif isinstance(m, dict):
            name = (m.get("name") or "").strip()
            email = (m.get("email") or None)
            email = email.strip() if isinstance(email, str) else None
            if name:
                normalized.append(Member(name=name, email=email or None))
    return normalized


@app.post("/auth/signup", status_code=201)
async def auth_signup(req: SignupIn) -> Dict[str, Any]:
    # Additional per-field validation to mirror frontend rules
    errors: Dict[str, str] = {}
    # Require either full_name or first+last
    prof = req.profile.model_dump() if req.profile else {}
    has_full = bool((prof.get("full_name") or "").strip())
    has_first_last = bool((prof.get("first_name") or "").strip()) and bool((prof.get("last_name") or "").strip())
    if not (has_full or has_first_last):
        errors["name"] = "Provide either Full Name or First and Last name"

    # Optional phone simple validation
    phone = (prof.get("phone") or "").strip()
    if phone and not re.match(r"^[+\d][\d\s().-]{6,}$", phone):
        errors["phone"] = "Invalid phone number"

    # Optional dob age check
    dob = prof.get("date_of_birth")
    if dob:
        try:
            y, m, d = map(int, dob.split("-"))
            born = date(y, m, d)
            today = date.today()
            age = today.year - born.year - (today < date(born.year, born.month, born.day))
            if age < 13:
                errors["date_of_birth"] = "Must be at least 13 years old"
        except Exception:
            errors["date_of_birth"] = "Invalid date format"

    # Optional zip check
    zipc = (prof.get("address", {}) or {}).get("zip") or ""
    if zipc and not re.match(r"^\d{5}(-\d{4})?$", zipc):
        errors["zip"] = "Invalid ZIP code"

    # Enforce unique email
    if Users.contains(Q.email == req.email):
        errors["email"] = "Email already registered"

    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    doc_id = Users.insert({
        "email": req.email,
        "password_hash": _hash_password(req.password),
        "profile": prof,
        "created_at": datetime.utcnow().isoformat(),
    })
    return {"id": doc_id, "email": req.email}


@app.post("/auth/login")
async def auth_login(req: LoginIn) -> Dict[str, Any]:
    doc = Users.get(Q.email == req.email)
    if not doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if doc.get("password_hash") != _hash_password(req.password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return {"ok": True}


@app.get("/auth/me", response_model=MeOut)
async def auth_me(x_user_email: Optional[str] = Header(default=None, alias="X-User-Email")) -> MeOut:
    """
    Demo auth: identify user by X-User-Email header (set by frontend after login).
    In production, replace with proper sessions/JWT.
    """
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email header")
    doc = Users.get(Q.email == x_user_email)
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    prof = doc.get("profile") or None
    # Normalize address keys presence
    if prof and isinstance(prof.get("address"), dict):
        prof["address"] = {
            "city": prof["address"].get("city"),
            "state": prof["address"].get("state"),
            "zip": prof["address"].get("zip"),
        }
    return MeOut(email=doc.get("email"), profile=Profile(**prof) if prof else None)


def _validate_profile(profile: Dict[str, Any]) -> Dict[str, str]:
    errors: Dict[str, str] = {}
    has_full = bool((profile.get("full_name") or "").strip())
    has_first_last = bool((profile.get("first_name") or "").strip()) and bool((profile.get("last_name") or "").strip())
    if not (has_full or has_first_last):
        errors["name"] = "Provide either Full Name or First and Last name"

    phone = (profile.get("phone") or "").strip()
    if phone and not re.match(r"^[+\d][\d\s().-]{6,}$", phone):
        errors["phone"] = "Invalid phone number"

    dob = profile.get("date_of_birth")
    if dob:
        try:
            y, m, d = map(int, dob.split("-"))
            born = date(y, m, d)
            today = date.today()
            age = today.year - born.year - (today < date(born.year, born.month, born.day))
            if age < 13:
                errors["date_of_birth"] = "Must be at least 13 years old"
        except Exception:
            errors["date_of_birth"] = "Invalid date format"

    zipc = (profile.get("address", {}) or {}).get("zip") or ""
    if zipc and not re.match(r"^\d{5}(-\d{4})?$", zipc):
        errors["zip"] = "Invalid ZIP code"
    return errors


class ProfilePatch(BaseModel):
    full_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    address: Optional[Dict[str, Optional[str]]] = None


class MePatchIn(BaseModel):
    profile: ProfilePatch


@app.patch("/auth/me", response_model=MeOut)
async def auth_me_update(payload: MePatchIn, x_user_email: Optional[str] = Header(default=None, alias="X-User-Email")) -> MeOut:
    if not x_user_email:
        raise HTTPException(status_code=401, detail="Missing X-User-Email header")
    doc = Users.get(Q.email == x_user_email)
    if not doc:
        raise HTTPException(status_code=404, detail="User not found")
    existing = doc.get("profile") or {}
    incoming = payload.profile.model_dump(exclude_unset=True)
    # Merge
    merged: Dict[str, Any] = {**existing}
    for k, v in incoming.items():
        if k == "address" and isinstance(v, dict):
            merged_addr = {**(existing.get("address") or {})}
            merged_addr.update({kk: vv for kk, vv in v.items() if vv is not None})
            merged["address"] = merged_addr
        else:
            merged[k] = v

    errors = _validate_profile(merged)
    if errors:
        raise HTTPException(status_code=422, detail={"errors": errors})

    Users.update({"profile": merged}, Q.email == x_user_email)
    return MeOut(email=x_user_email, profile=Profile(**merged))


@app.get("/groups", response_model=List[Group])
async def list_groups() -> List[Group]:
    items = Groups.all()
    result: List[Group] = []
    for doc in items:
        members = _normalize_members(doc.get("members", []))
        result.append(
            Group(
                id=doc.doc_id,
                name=doc.get("name"),
                members=members,
                days=doc.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
                cycle_days=doc.get("cycle_days", 10),
            )
        )
    return result


@app.get("/groups/{name}", response_model=Optional[Group])
async def get_group(name: str) -> Optional[Group]:
    doc = Groups.get(Q.name == name)
    if not doc:
        raise HTTPException(status_code=404, detail="Group not found")
    members = _normalize_members(doc.get("members", []))
    return Group(
        id=doc.doc_id,
        name=doc.get("name"),
        members=members,
        days=doc.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]),
        cycle_days=doc.get("cycle_days", 10),
    )


@app.post("/groups", status_code=201, response_model=Group)
async def create_group(group: GroupIn) -> Group:
    # Enforce unique name
    if Groups.contains(Q.name == group.name):
        raise HTTPException(status_code=409, detail="Group name already exists")

    doc_id = Groups.insert({
        "name": group.name,
        "members": [m.model_dump() for m in group.members],
        "days": group.days,
        "cycle_days": group.cycle_days,
    })
    return Group(id=doc_id, name=group.name, members=group.members, days=group.days, cycle_days=group.cycle_days)


@app.delete("/groups/{name}", status_code=204)
async def delete_group(name: str):
    removed = Groups.remove(Q.name == name)
    if not removed:
        raise HTTPException(status_code=404, detail="Group not found")
    return None


@app.get("/groups/{name}/schedule", response_model=Optional[StoredSchedule])
async def get_saved_schedule(name: str) -> Optional[StoredSchedule]:
    doc = Groups.get(Q.name == name)
    if not doc:
        raise HTTPException(status_code=404, detail="Group not found")
    sched = doc.get("schedule")
    if not sched:
        raise HTTPException(status_code=404, detail="No schedule for this group")
    try:
        items = [ScheduleItem(date=date.fromisoformat(i["date"]) if isinstance(i["date"], str) else i["date"], driver=i["driver"]) for i in sched.get("items", [])]
        return StoredSchedule(
            start_date=date.fromisoformat(sched["start_date"]) if isinstance(sched["start_date"], str) else sched["start_date"],
            end_date=date.fromisoformat(sched["end_date"]) if isinstance(sched["end_date"], str) else sched["end_date"],
            items=items,
        )
    except Exception:
        raise HTTPException(status_code=500, detail="Corrupted schedule data")


@app.post("/groups/{name}/schedule", response_model=List[ScheduleItem])
async def generate_schedule(name: str, req: ScheduleRequest) -> List[ScheduleItem]:
    """
    Generate a balanced rotation schedule for the given group starting at start_date.
    - Uses group's members (order as stored), selected weekdays, and cycle_days (10/20/30).
    - Total slots = ceil(cycle_days / len(members)) * len(members) to balance turns.
    - Only includes dates that fall on the group's selected weekdays, starting from start_date inclusive.
    - If an active schedule exists (today <= end_date), do not regenerate and return 409.
    """
    doc = Groups.get(Q.name == name)
    if not doc:
        raise HTTPException(status_code=404, detail="Group not found")

    # Prevent regeneration if active schedule exists
    existing = doc.get("schedule")
    if existing:
        try:
            end_date = date.fromisoformat(existing["end_date"]) if isinstance(existing["end_date"], str) else existing["end_date"]
            if date.today() <= end_date:
                # Include existing schedule in the error detail for client to render
                raise HTTPException(
                    status_code=409,
                    detail={
                        "message": f"Schedule already generated and active until {end_date.isoformat()}",
                        "schedule": existing,
                    },
                )
        except KeyError:
            pass

    members_objs = _normalize_members(doc.get("members", []))
    if not members_objs:
        raise HTTPException(status_code=400, detail="Group has no members")
    # Use names for drivers
    members: List[str] = [m.name for m in members_objs]

    days: List[str] = doc.get("days", ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"])
    allowed_idx = {WEEKDAY_NAME_TO_INDEX[d] for d in days if d in WEEKDAY_NAME_TO_INDEX}
    if not allowed_idx:
        raise HTTPException(status_code=400, detail="Group has no valid weekdays configured")

    cycle_days: int = int(doc.get("cycle_days", 10))
    # Compute total slots rounded up to equalize turns
    n = len(members)
    rounds = (cycle_days + n - 1) // n
    total_slots = rounds * n

    # Walk forward from start_date over calendar days, picking only configured weekdays
    cur = req.start_date
    slots: List[date] = []
    while len(slots) < total_slots:
        if cur.weekday() in allowed_idx:
            slots.append(cur)
        cur += timedelta(days=1)

    # Assign drivers in round-robin order based on storage order
    schedule: List[ScheduleItem] = []
    for i, d in enumerate(slots):
        driver = members[i % n]
        schedule.append(ScheduleItem(date=d, driver=driver))

    # Persist schedule on the group
    end = slots[-1] if slots else req.start_date
    Groups.update({
        "schedule": {
            "start_date": req.start_date.isoformat(),
            "end_date": end.isoformat(),
            "items": [{"date": s.date.isoformat(), "driver": s.driver} for s in schedule],
        }
    }, doc_ids=[doc.doc_id])

    return schedule


@app.post("/on_demand/requests", status_code=201, response_model=OnDemandRequest)
async def create_on_demand(req: OnDemandRequestIn) -> OnDemandRequest:
    doc_id = OnDemand.insert({
        "origin_lat": req.origin_lat,
        "origin_lng": req.origin_lng,
        "destination": req.destination,
        "dest_lat": req.dest_lat,
        "dest_lng": req.dest_lng,
        "dest_place_id": req.dest_place_id,
        "dest_address": req.dest_address,
        "created_at": datetime.utcnow().isoformat(),
    })
    return OnDemandRequest(id=doc_id, created_at=datetime.utcnow(), **req.model_dump())


@app.get("/on_demand/requests", response_model=List[OnDemandRequest])
async def list_on_demand() -> List[OnDemandRequest]:
    items = OnDemand.all()
    result: List[OnDemandRequest] = []
    for doc in items:
        result.append(
            OnDemandRequest(
                id=doc.doc_id,
                origin_lat=doc.get("origin_lat"),
                origin_lng=doc.get("origin_lng"),
                destination=doc.get("destination", ""),
                dest_lat=doc.get("dest_lat"),
                dest_lng=doc.get("dest_lng"),
                dest_place_id=doc.get("dest_place_id"),
                dest_address=doc.get("dest_address"),
                created_at=datetime.fromisoformat(doc.get("created_at")) if isinstance(doc.get("created_at"), str) else (doc.get("created_at") or datetime.utcnow()),
            )
        )
    # Sort newest first
    result.sort(key=lambda r: r.created_at, reverse=True)
    return result


# Optional root route for quick check
@app.get("/")
async def root() -> dict:
    return {"service": "carpool", "version": "0.1.0"}
