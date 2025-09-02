from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator
from tinydb import TinyDB, Query
from datetime import date, timedelta

# Initialize FastAPI app
app = FastAPI(title="Carpool API", version="0.1.0")

# Configure CORS for local dev (Vite default port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
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
Q = Query()

WEEKDAY_NAME_TO_INDEX = {
    "Monday": 0,
    "Tuesday": 1,
    "Wednesday": 2,
    "Thursday": 3,
    "Friday": 4,
}

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


# Optional root route for quick check
@app.get("/")
async def root() -> dict:
    return {"service": "carpool", "version": "0.1.0"}
