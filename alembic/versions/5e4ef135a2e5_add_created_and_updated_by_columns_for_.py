"""add created and updated by columns for pets

Revision ID: 5e4ef135a2e5
Revises: 76ae04625217
Create Date: 2023-12-20 08:13:43.239005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e4ef135a2e5'
down_revision = '76ae04625217'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pets', sa.Column('created_by', sa.String(), nullable=True))
    op.add_column('pets', sa.Column('updated_by', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'pets', ['unique_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'pets', type_='unique')
    op.drop_column('pets', 'updated_by')
    op.drop_column('pets', 'created_by')
    # ### end Alembic commands ###
