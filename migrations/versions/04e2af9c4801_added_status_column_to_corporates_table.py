"""Added status column to corporates table

Revision ID: 04e2af9c4801
Revises: 82807ee2bd62
Create Date: 2026-07-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '04e2af9c4801'
down_revision = '82807ee2bd62'
branch_labels = None
depends_on = None


def upgrade():
    # 1. Fix the staff table status column to ENUM
    with op.batch_alter_table('staff', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.Enum('ACTIVE', 'INACTIVE', name='status'),
               existing_nullable=True)

    # 2. SKIPPED: corporates table already has the status column manually added
    # with op.batch_alter_table('corporates', schema=None) as batch_op:
    #     batch_op.add_column(sa.Column('status', sa.Enum('ACTIVE', 'INACTIVE', name='status'), nullable=False))


def downgrade():
    # SKIPPED: 
    # with op.batch_alter_table('corporates', schema=None) as batch_op:
    #     batch_op.drop_column('status')

    # Revert staff table status column back to VARCHAR
    with op.batch_alter_table('staff', schema=None) as batch_op:
        batch_op.alter_column('status',
               existing_type=sa.Enum('ACTIVE', 'INACTIVE', name='status'),
               type_=sa.VARCHAR(length=50),
               existing_nullable=True)