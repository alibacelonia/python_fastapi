"""initial

Revision ID: f0974aab788d
Revises: 
Create Date: 2023-11-25 08:40:37.010477

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f0974aab788d'
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
    sa.UniqueConstraint('type'),
    sa.UniqueConstraint('type_id')
    )
    op.create_table('users',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('firstname', sa.String(), nullable=True),
    sa.Column('lastname', sa.String(), nullable=True),
    sa.Column('street_address', sa.String(), nullable=True),
    sa.Column('postal_code', sa.String(), nullable=True),
    sa.Column('city_code', sa.String(), nullable=True),
    sa.Column('city', sa.String(), nullable=True),
    sa.Column('state_code', sa.String(), nullable=True),
    sa.Column('state', sa.String(), nullable=True),
    sa.Column('country_code', sa.String(), nullable=True),
    sa.Column('country', sa.String(), nullable=True),
    sa.Column('phone_number', sa.String(), nullable=True),
    sa.Column('photo', sa.String(), nullable=True),
    sa.Column('secondary_contact', sa.String(), nullable=True),
    sa.Column('secondary_contact_number', sa.String(), nullable=True),
    sa.Column('verified', sa.Boolean(), server_default='False', nullable=False),
    sa.Column('verification_code', sa.String(), nullable=True),
    sa.Column('role', sa.String(), server_default='user', nullable=False),
    sa.Column('email', sa.String(), nullable=False),
    sa.Column('password', sa.String(), nullable=False),
    sa.Column('otp', sa.String(), nullable=True),
    sa.Column('otp_secret', sa.String(), nullable=True),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('email'),
    sa.UniqueConstraint('phone_number')
    )
    op.create_table('pets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('unique_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('microchip_id', sa.String(), nullable=True),
    sa.Column('name', sa.String(), nullable=True),
    sa.Column('description', sa.String(), nullable=True),
    sa.Column('behavior', sa.String(), nullable=True),
    sa.Column('weight', sa.Float(), nullable=True),
    sa.Column('gender', sa.String(), nullable=True),
    sa.Column('color', sa.String(), nullable=True),
    sa.Column('pet_type_id', sa.Integer(), nullable=True),
    sa.Column('main_picture', sa.String(), nullable=True),
    sa.Column('breed', sa.String(), nullable=True),
    sa.Column('date_of_birth_month', sa.Integer(), nullable=True),
    sa.Column('date_of_birth_year', sa.Integer(), nullable=True),
    sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['pet_type_id'], ['pet_type.type_id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_pets_microchip_id'), 'pets', ['microchip_id'], unique=False)
    op.create_index(op.f('ix_pets_name'), 'pets', ['name'], unique=False)
    op.create_table('posts',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('title', sa.String(), nullable=False),
    sa.Column('content', sa.String(), nullable=False),
    sa.Column('category', sa.String(), nullable=False),
    sa.Column('image', sa.String(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('pet_images',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('path', sa.String(length=255), nullable=False),
    sa.Column('pet_id', sa.Integer(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['pet_id'], ['pets.id'], ),
    sa.PrimaryKeyConstraint('id', 'pet_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('pet_images')
    op.drop_table('posts')
    op.drop_index(op.f('ix_pets_name'), table_name='pets')
    op.drop_index(op.f('ix_pets_microchip_id'), table_name='pets')
    op.drop_table('pets')
    op.drop_table('users')
    op.drop_table('pet_type')
    # ### end Alembic commands ###
