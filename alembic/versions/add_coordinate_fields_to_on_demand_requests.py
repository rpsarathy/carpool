"""add coordinate fields to on_demand_requests

Revision ID: add_coordinate_fields
Revises: add_google_oauth
Create Date: 2025-09-15 14:52:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_coordinate_fields'
down_revision = 'add_google_oauth'
branch_labels = None
depends_on = None


def upgrade():
    # Create on_demand_requests table if it doesn't exist
    op.create_table('on_demand_requests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_email', sa.String(), nullable=False),
        sa.Column('origin', sa.String(), nullable=False),
        sa.Column('origin_lat', sa.Float(), nullable=True),
        sa.Column('origin_lng', sa.Float(), nullable=True),
        sa.Column('destination', sa.String(), nullable=False),
        sa.Column('dest_lat', sa.Float(), nullable=True),
        sa.Column('dest_lng', sa.Float(), nullable=True),
        sa.Column('dest_place_id', sa.String(), nullable=True),
        sa.Column('dest_address', sa.String(), nullable=True),
        sa.Column('date', sa.String(), nullable=False),
        sa.Column('preferred_driver', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_on_demand_requests_id'), 'on_demand_requests', ['id'], unique=False)


def downgrade():
    # Drop the entire table
    op.drop_index(op.f('ix_on_demand_requests_id'), table_name='on_demand_requests')
    op.drop_table('on_demand_requests')
