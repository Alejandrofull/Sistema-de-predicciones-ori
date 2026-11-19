from datetime import date
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.inventory_intervention import InventoryIntervention
from app.models.recipe_ingredient import RecipeIngredient
from app.repositories.business_series_repository import BusinessSeriesRepository
from app.security.permissions import Permissions, require_permission

router = APIRouter(prefix="/inventory", tags=["inventory setup"])

class InterventionIn(BaseModel):
    start_date: date
    description: str = Field(min_length=3, max_length=500)

class IngredientIn(BaseModel):
    ingredient_series_id: int = Field(gt=0)
    quantity_per_dish: float = Field(gt=0)

class RecipeIn(BaseModel):
    ingredients: list[IngredientIn] = Field(min_length=1)

@router.get("/intervention")
def intervention(db: Session = Depends(get_db), user=Depends(require_permission(Permissions.INVENTORY_VIEW))):
    entry = db.scalars(select(InventoryIntervention).order_by(InventoryIntervention.start_date)).first()
    return {"start_date": entry.start_date, "description": entry.description} if entry else None

@router.put("/intervention")
def set_intervention(body: InterventionIn, db: Session = Depends(get_db), user=Depends(require_permission(Permissions.INVENTORY_MANAGE))):
    from app.models.inventory_observation import InventoryObservation
    rows = db.scalars(select(InventoryObservation)).all()
    keys = [(row.business_series_id, row.observation_date) for row in rows]
    if len(keys) != len(set(keys)):
        raise HTTPException(409, "Hay observaciones PRE/POST duplicadas para el mismo producto y fecha")
    existing = db.scalars(select(InventoryIntervention)).all()
    if existing:
        entry = existing[0]
        entry.start_date, entry.description = body.start_date, body.description
        # Remove extra intervention dates to enforce one global cutoff.
        for extra in existing[1:]: db.delete(extra)
    else:
        entry = InventoryIntervention(start_date=body.start_date, description=body.description, created_by=user.id)
        db.add(entry)
    db.commit()
    # Reclassify old rows to avoid PRE/POST discrepancies.
    from app.models.inventory_observation import InventoryObservation
    rows = db.scalars(select(InventoryObservation)).all()
    for obs in rows:
        obs.phase = "post" if obs.observation_date >= body.start_date else "pre"
    db.commit()
    return {"start_date": body.start_date, "description": body.description}

@router.get("/recipes/{dish_series_id}")
def get_recipe(dish_series_id: int, db: Session = Depends(get_db), user=Depends(require_permission(Permissions.INVENTORY_VIEW))):
    items = db.scalars(select(RecipeIngredient).where(RecipeIngredient.dish_series_id == dish_series_id)).all()
    return [{"ingredient_series_id": x.ingredient_series_id, "quantity_per_dish": x.quantity_per_dish} for x in items]

@router.put("/recipes/{dish_series_id}")
def put_recipe(dish_series_id: int, body: RecipeIn, db: Session = Depends(get_db), user=Depends(require_permission(Permissions.INVENTORY_MANAGE))):
    if not BusinessSeriesRepository.get_by_id(db, dish_series_id): raise HTTPException(404, "Plato no encontrado")
    ids = [x.ingredient_series_id for x in body.ingredients]
    if dish_series_id in ids or len(set(ids)) != len(ids): raise HTTPException(422, "Ingredientes duplicados o receta autorreferente")
    if any(not BusinessSeriesRepository.get_by_id(db, i) for i in ids): raise HTTPException(422, "Insumo no encontrado")
    db.execute(delete(RecipeIngredient).where(RecipeIngredient.dish_series_id == dish_series_id))
    for x in body.ingredients: db.add(RecipeIngredient(dish_series_id=dish_series_id, ingredient_series_id=x.ingredient_series_id, quantity_per_dish=x.quantity_per_dish))
    db.commit()
    return {"dish_series_id": dish_series_id, "ingredients": body.ingredients}

@router.get("/recipes/{dish_series_id}/requirements")
def requirements(dish_series_id: int, planned_dishes: float = 1, db: Session = Depends(get_db), user=Depends(require_permission(Permissions.INVENTORY_VIEW))):
    if planned_dishes < 0: raise HTTPException(422, "Cantidad planificada inválida")
    items = db.scalars(select(RecipeIngredient).where(RecipeIngredient.dish_series_id == dish_series_id)).all()
    return [{"ingredient_series_id": x.ingredient_series_id, "required_quantity": x.quantity_per_dish * planned_dishes} for x in items]
