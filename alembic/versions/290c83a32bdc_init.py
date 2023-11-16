"""init

Revision ID: 290c83a32bdc
Revises: 
Create Date: 2023-11-04 03:26:13.832716

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '290c83a32bdc'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('pet_type',
    sa.Column('type_id', sa.Integer(), nullable=False),
    sa.Column('type', sa.String(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('type_id'),
    sa.UniqueConstraint('type_id')
    )
    
    # Inserting data
    op.execute("INSERT INTO pet_type (type) VALUES ('dog'), ('cat')")
    
    op.create_foreign_key(None, 'pets', 'pet_type', ['pet_type_id'], ['type_id'])
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint(None, 'pets', type_='foreignkey')
    op.drop_table('pet_type')
    # ### end Alembic commands ###