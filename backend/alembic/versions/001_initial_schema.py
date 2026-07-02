"""Initial schema for Insta-data PostgreSQL.

Revision ID: 001
Revises:
Create Date: 2026-06-16 12:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial tables."""
    # Create price_history table
    op.create_table(
        'price_history',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(24), nullable=False),
        sa.Column('product_name', sa.String(500), nullable=False),
        sa.Column('store', sa.String(50), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False, server_default='EUR'),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for price_history
    op.create_index(
        'idx_product_store_timestamp',
        'price_history',
        ['product_id', 'store', 'timestamp'],
        unique=False
    )
    op.create_index(
        'idx_store_timestamp',
        'price_history',
        ['store', 'timestamp'],
        unique=False
    )
    op.create_index(
        'idx_timestamp',
        'price_history',
        ['timestamp'],
        unique=False
    )
    op.create_index(
        'idx_product_id',
        'price_history',
        ['product_id'],
        unique=False
    )

    # Create scraper_logs table
    op.create_table(
        'scraper_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('scraper_name', sa.String(50), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('products_found', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('products_saved', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('errors', sa.String(2000), nullable=True),
        sa.Column('duration_seconds', sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for scraper_logs
    op.create_index(
        'idx_scraper_timestamp',
        'scraper_logs',
        ['scraper_name', 'start_time'],
        unique=False
    )
    op.create_index(
        'idx_scraper_status',
        'scraper_logs',
        ['scraper_name', 'status'],
        unique=False
    )


def downgrade() -> None:
    """Drop initial tables."""
    op.drop_index('idx_scraper_status', table_name='scraper_logs')
    op.drop_index('idx_scraper_timestamp', table_name='scraper_logs')
    op.drop_table('scraper_logs')

    op.drop_index('idx_product_id', table_name='price_history')
    op.drop_index('idx_timestamp', table_name='price_history')
    op.drop_index('idx_store_timestamp', table_name='price_history')
    op.drop_index('idx_product_store_timestamp', table_name='price_history')
    op.drop_table('price_history')