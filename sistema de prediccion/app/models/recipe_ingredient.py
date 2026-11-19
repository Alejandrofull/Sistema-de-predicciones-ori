from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base import Base

class RecipeIngredient(Base):
    __tablename__ = "recipe_ingredients"
    __table_args__ = (UniqueConstraint("dish_series_id", "ingredient_series_id", name="uq_recipe_dish_ingredient"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dish_series_id: Mapped[int] = mapped_column(ForeignKey("business_series.id", ondelete="CASCADE"), nullable=False)
    ingredient_series_id: Mapped[int] = mapped_column(ForeignKey("business_series.id", ondelete="CASCADE"), nullable=False)
    quantity_per_dish: Mapped[float] = mapped_column(Float, nullable=False)
