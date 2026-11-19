"""Operational inventory, intervention and recipe data."""
from alembic import op
import sqlalchemy as sa
revision = 'd29e4d7f8a10'
down_revision = '96df3fcee827'
branch_labels = None
depends_on = None

def upgrade():
    for name, typ in [
        ('waste_quantity', sa.Float()), ('max_operating_stock', sa.Float()),
        ('planned_quantity', sa.Float()), ('complete_requirements', sa.Integer()),
        ('total_requirements', sa.Integer()),
    ]: op.add_column('inventory_observations', sa.Column(name, typ, nullable=True))
    op.create_table('inventory_interventions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_table('recipe_ingredients',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('dish_series_id', sa.Integer(), sa.ForeignKey('business_series.id', ondelete='CASCADE'), nullable=False),
        sa.Column('ingredient_series_id', sa.Integer(), sa.ForeignKey('business_series.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity_per_dish', sa.Float(), nullable=False),
        sa.UniqueConstraint('dish_series_id', 'ingredient_series_id', name='uq_recipe_dish_ingredient'))

def downgrade():
    op.drop_table('recipe_ingredients')
    op.drop_table('inventory_interventions')
    for name in ('total_requirements','complete_requirements','planned_quantity','max_operating_stock','waste_quantity'):
        op.drop_column('inventory_observations',name)
