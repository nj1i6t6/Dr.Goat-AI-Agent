"""add cost and revenue entry tables"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '9c5e8de17c3f'
down_revision = '8f3d184d9c4a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'cost_entry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=120), nullable=False),
        sa.Column('subcategory', sa.String(length=120), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('currency', sa.String(length=16), nullable=False, server_default='TWD'),
        sa.Column('recorded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('breed', sa.String(length=100), nullable=True),
        sa.Column('age_group', sa.String(length=50), nullable=True),
        sa.Column('parity', sa.Integer(), nullable=True),
        sa.Column('herd_tag', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_cost_entry_user_category', 'cost_entry', ['user_id', 'category'], unique=False)
    op.create_index('ix_cost_entry_user_recorded_at', 'cost_entry', ['user_id', 'recorded_at'], unique=False)
    op.create_index('ix_cost_entry_user_breed', 'cost_entry', ['user_id', 'breed'], unique=False)

    op.create_table(
        'revenue_entry',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=120), nullable=False),
        sa.Column('subcategory', sa.String(length=120), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('currency', sa.String(length=16), nullable=False, server_default='TWD'),
        sa.Column('recorded_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('breed', sa.String(length=100), nullable=True),
        sa.Column('age_group', sa.String(length=50), nullable=True),
        sa.Column('parity', sa.Integer(), nullable=True),
        sa.Column('herd_tag', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_revenue_entry_user_category', 'revenue_entry', ['user_id', 'category'], unique=False)
    op.create_index('ix_revenue_entry_user_recorded_at', 'revenue_entry', ['user_id', 'recorded_at'], unique=False)
    op.create_index('ix_revenue_entry_user_breed', 'revenue_entry', ['user_id', 'breed'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_revenue_entry_user_breed', table_name='revenue_entry')
    op.drop_index('ix_revenue_entry_user_recorded_at', table_name='revenue_entry')
    op.drop_index('ix_revenue_entry_user_category', table_name='revenue_entry')
    op.drop_table('revenue_entry')

    op.drop_index('ix_cost_entry_user_breed', table_name='cost_entry')
    op.drop_index('ix_cost_entry_user_recorded_at', table_name='cost_entry')
    op.drop_index('ix_cost_entry_user_category', table_name='cost_entry')
    op.drop_table('cost_entry')
