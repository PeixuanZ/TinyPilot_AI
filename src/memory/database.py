"""
Week 1: Structured event store using SQLite + SQLAlchemy
Stores feeding, sleep, growth, milestones, medical, notes
"""
from sqlalchemy import (
    create_engine, Column, String, Float,
    DateTime, JSON, Integer, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from pathlib import Path
import uuid

ROOT_DIR = Path(__file__).parent.parent.parent
DB_PATH  = ROOT_DIR / "data" / "db" / "tinypilot.db"
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

engine  = create_engine(f"sqlite:///{DB_PATH}", echo=False)
Session = sessionmaker(bind=engine)
Base    = declarative_base()


class Event(Base):
    __tablename__ = "events"

    id         = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    event_type = Column(String, nullable=False)   # feeding, sleep, growth, milestone, medical, note
    date       = Column(DateTime, default=datetime.utcnow)
    data       = Column(JSON, nullable=False)      # flexible payload
    notes      = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def init_db():
    Base.metadata.create_all(engine)
    print(f"✓ Database initialized at {DB_PATH}")


def add_event(event_type: str, data: dict, notes: str = None, date: datetime = None) -> str:
    """Insert a new event into the database."""
    session = Session()
    event = Event(
        event_type = event_type,
        date       = date or datetime.utcnow(),
        data       = data,
        notes      = notes
    )
    session.add(event)
    session.commit()
    event_id = event.id
    session.close()
    return event_id


def get_events(event_type: str = None, limit: int = 100) -> list:
    """Retrieve events, optionally filtered by type."""
    session = Session()
    query   = session.query(Event)
    if event_type:
        query = query.filter(Event.event_type == event_type)
    events = query.order_by(Event.date.desc()).limit(limit).all()
    result = [
        {
            "id":         e.id,
            "event_type": e.event_type,
            "date":       e.date.isoformat(),
            "data":       e.data,
            "notes":      e.notes
        }
        for e in events
    ]
    session.close()
    return result


def get_events_by_date_range(
    start: datetime, end: datetime,
    event_type: str = None
) -> list:
    """Retrieve events within a date range."""
    session = Session()
    query   = session.query(Event).filter(
        Event.date >= start,
        Event.date <= end
    )
    if event_type:
        query = query.filter(Event.event_type == event_type)
    events = query.order_by(Event.date.asc()).all()
    result = [
        {
            "id":         e.id,
            "event_type": e.event_type,
            "date":       e.date.isoformat(),
            "data":       e.data,
            "notes":      e.notes
        }
        for e in events
    ]
    session.close()
    return result


if __name__ == "__main__":
    init_db()

    from datetime import timedelta

    print("\nInserting test events...")

    # Feeding events
    for i in range(5):
        add_event(
            "feeding",
            data={"food": ["breast milk", "oatmeal", "banana", "salmon", "yogurt"][i],
                  "amount_ml": [120, 80, 50, 60, 90][i]},
            date=datetime.utcnow() - timedelta(days=i)
        )

    # Sleep events
    for i in range(3):
        add_event(
            "sleep",
            data={"duration_hours": [10.5, 9.0, 11.0][i],
                  "night_wakings": [1, 3, 0][i]},
            date=datetime.utcnow() - timedelta(days=i)
        )

    # Growth
    add_event("growth", data={"weight_kg": 7.2, "height_cm": 68.0})

    # Milestone
    add_event("milestone", data={"milestone": "first steps", "age_months": 11})

    # Verify
    print("\nAll events:")
    for e in get_events():
        print(f"  [{e['event_type']}] {e['date'][:10]} — {e['data']}")