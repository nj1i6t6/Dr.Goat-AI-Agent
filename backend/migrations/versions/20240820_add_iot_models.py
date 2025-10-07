"""add iot device and automation tables"""

from alembic import op
import sqlalchemy as sa


revision = '20240820_add_iot_models'
down_revision = '20240723_add_core_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'iot_device',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('device_type', sa.String(length=120), nullable=False),
        sa.Column('category', sa.String(length=20), nullable=False),
        sa.Column('location', sa.String(length=120)),
        sa.Column('control_url', sa.String(length=255)),
        sa.Column('status', sa.String(length=32), nullable=False, server_default=sa.text("'offline'")),
        sa.Column('last_seen', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('api_key', sa.String(length=255), nullable=False),
        sa.Column('api_key_hint', sa.String(length=32)),
    )
    op.create_index('ix_iot_device_user_category', 'iot_device', ['user_id', 'category'])

    op.create_table(
        'sensor_reading',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('device_id', sa.Integer(), sa.ForeignKey('iot_device.id', ondelete='CASCADE'), nullable=False),
        sa.Column('data', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_sensor_reading_device_created_at', 'sensor_reading', ['device_id', 'created_at'])

    op.create_table(
        'automation_rule',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('user.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('trigger_source_device_id', sa.Integer(), sa.ForeignKey('iot_device.id', ondelete='CASCADE'), nullable=False),
        sa.Column('trigger_condition', sa.JSON(), nullable=False),
        sa.Column('action_target_device_id', sa.Integer(), sa.ForeignKey('iot_device.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action_command', sa.JSON(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default=sa.text('1')),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_automation_rule_user_enabled', 'automation_rule', ['user_id', 'is_enabled'])

    op.create_table(
        'device_control_log',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('rule_id', sa.Integer(), sa.ForeignKey('automation_rule.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_device_id', sa.Integer(), sa.ForeignKey('iot_device.id', ondelete='CASCADE'), nullable=False),
        sa.Column('command', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default=sa.text("'pending'")),
        sa.Column('response_payload', sa.JSON()),
        sa.Column('executed_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
    )
    op.create_index('ix_device_control_log_rule', 'device_control_log', ['rule_id', 'executed_at'])


def downgrade() -> None:
    op.drop_index('ix_device_control_log_rule', table_name='device_control_log')
    op.drop_table('device_control_log')

    op.drop_index('ix_automation_rule_user_enabled', table_name='automation_rule')
    op.drop_table('automation_rule')

    op.drop_index('ix_sensor_reading_device_created_at', table_name='sensor_reading')
    op.drop_table('sensor_reading')

    op.drop_index('ix_iot_device_user_category', table_name='iot_device')
    op.drop_table('iot_device')
