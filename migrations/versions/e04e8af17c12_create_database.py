"""create database

Revision ID: e04e8af17c12
Revises: 
Create Date: 2021-02-08 18:55:19.689870

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e04e8af17c12'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('scheduled_tasks',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('start', sa.DateTime(), nullable=False),
    sa.Column('interval', sa.Integer(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('cancelled', sa.Boolean(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_scheduled_tasks_name'), 'scheduled_tasks', ['name'], unique=False)
    op.create_table('users',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('username', sa.Text(), nullable=False),
    sa.Column('password_hash', sa.Text(), nullable=False),
    sa.Column('telephone', sa.Integer(), nullable=False),
    sa.Column('paid', sa.Boolean(), nullable=False),
    sa.Column('date_paid', sa.DateTime(), nullable=True),
    sa.Column('creation_date', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('telephone')
    )
    op.create_table('payments',
    sa.Column('code', sa.Text(), nullable=False),
    sa.Column('sender', sa.Text(), nullable=True),
    sa.Column('creation_date', sa.DateTime(), nullable=True),
    sa.Column('amount', sa.Text(), nullable=True),
    sa.Column('User', sa.String(length=60), nullable=True),
    sa.Column('scheduled_task_id', sa.String(length=36), nullable=True),
    sa.ForeignKeyConstraint(['User'], ['users.telephone'], onupdate='CASCADE', ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('code')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('payments')
    op.drop_table('users')
    op.drop_index(op.f('ix_scheduled_tasks_name'), table_name='scheduled_tasks')
    op.drop_table('scheduled_tasks')
    # ### end Alembic commands ###