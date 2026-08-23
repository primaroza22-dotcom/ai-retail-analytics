"""add cameras and camera_id

Revision ID: 532a4322b832
Revises: 2201ab1ba855
Create Date: 2026-08-23 13:44:49.609184

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = '532a4322b832'
down_revision = '2201ab1ba855'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cameras',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=False),
        sa.Column('source_url', sa.String(), nullable=True),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_cameras'),
    )

    with op.batch_alter_table('dwell_sessions') as batch_op:
        batch_op.add_column(sa.Column('camera_id', sa.String(), nullable=True))
        batch_op.create_index('ix_dwell_sessions_camera_id', ['camera_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_dwell_sessions_camera_id_cameras', 'cameras', ['camera_id'], ['id']
        )

    with op.batch_alter_table('zone_events') as batch_op:
        batch_op.add_column(sa.Column('camera_id', sa.String(), nullable=True))
        batch_op.create_index('ix_zone_events_camera_id', ['camera_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_zone_events_camera_id_cameras', 'cameras', ['camera_id'], ['id']
        )

    with op.batch_alter_table('zones') as batch_op:
        batch_op.add_column(sa.Column('camera_id', sa.String(), nullable=True))
        batch_op.create_index('ix_zones_camera_id', ['camera_id'], unique=False)
        batch_op.create_foreign_key(
            'fk_zones_camera_id_cameras', 'cameras', ['camera_id'], ['id']
        )


def downgrade() -> None:
    with op.batch_alter_table('zones') as batch_op:
        batch_op.drop_constraint('fk_zones_camera_id_cameras', type_='foreignkey')
        batch_op.drop_index('ix_zones_camera_id')
        batch_op.drop_column('camera_id')

    with op.batch_alter_table('zone_events') as batch_op:
        batch_op.drop_constraint('fk_zone_events_camera_id_cameras', type_='foreignkey')
        batch_op.drop_index('ix_zone_events_camera_id')
        batch_op.drop_column('camera_id')

    with op.batch_alter_table('dwell_sessions') as batch_op:
        batch_op.drop_constraint('fk_dwell_sessions_camera_id_cameras', type_='foreignkey')
        batch_op.drop_index('ix_dwell_sessions_camera_id')
        batch_op.drop_column('camera_id')

    op.drop_table('cameras')
