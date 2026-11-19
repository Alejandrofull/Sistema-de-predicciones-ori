from datetime import date
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.inventory_intervention import InventoryIntervention

def resolve_phase(db: Session, day: date, manual_phase: str) -> str:
    """The earliest registered intervention marks PRE/POST for all observations."""
    date_start = db.scalar(select(InventoryIntervention.start_date).order_by(InventoryIntervention.start_date).limit(1))
    return ("post" if day >= date_start else "pre") if date_start else manual_phase
