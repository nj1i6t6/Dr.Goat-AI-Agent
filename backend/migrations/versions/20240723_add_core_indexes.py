"""add composite indexes for sheep domain tables"""

from alembic import op
import sqlalchemy as sa

revision = '20240723_add_core_indexes'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if 'sheep_event' in tables:
        existing = {index['name'] for index in inspector.get_indexes('sheep_event')}
        if 'ix_sheep_event_user_sheep_date' not in existing:
            op.create_index('ix_sheep_event_user_sheep_date', 'sheep_event', ['user_id', 'sheep_id', 'event_date'])
        if 'ix_sheep_event_user_type_date' not in existing:
            op.create_index('ix_sheep_event_user_type_date', 'sheep_event', ['user_id', 'event_type', 'event_date'])

    if 'sheep_historical_data' in tables:
        existing = {index['name'] for index in inspector.get_indexes('sheep_historical_data')}
        if 'ix_sheep_hist_user_type_date' not in existing:
            op.create_index('ix_sheep_hist_user_type_date', 'sheep_historical_data', ['user_id', 'record_type', 'record_date'])

    if 'sheep' in tables:
        existing = {index['name'] for index in inspector.get_indexes('sheep')}
        if 'ix_sheep_user_status' not in existing:
            op.create_index('ix_sheep_user_status', 'sheep', ['user_id', 'status'])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    tables = set(inspector.get_table_names())

    if 'sheep_event' in tables:
        existing = {index['name'] for index in inspector.get_indexes('sheep_event')}
        if 'ix_sheep_event_user_sheep_date' in existing:
            op.drop_index('ix_sheep_event_user_sheep_date', table_name='sheep_event')
        if 'ix_sheep_event_user_type_date' in existing:
            op.drop_index('ix_sheep_event_user_type_date', table_name='sheep_event')

    if 'sheep_historical_data' in tables:
        existing = {index['name'] for index in inspector.get_indexes('sheep_historical_data')}
        if 'ix_sheep_hist_user_type_date' in existing:
            op.drop_index('ix_sheep_hist_user_type_date', table_name='sheep_historical_data')

    if 'sheep' in tables:
        existing = {index['name'] for index in inspector.get_indexes('sheep')}
        if 'ix_sheep_user_status' in existing:
            op.drop_index('ix_sheep_user_status', table_name='sheep')
