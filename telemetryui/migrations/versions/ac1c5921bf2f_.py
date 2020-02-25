"""empty message

Revision ID: ac1c5921bf2f
Revises: 
Create Date: 2020-02-27 19:23:46.589251

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ac1c5921bf2f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('guilty',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('function', sa.String(), nullable=True),
    sa.Column('module', sa.String(), nullable=True),
    sa.Column('comment', sa.String(), nullable=True),
    sa.Column('hide', sa.Boolean(), nullable=False, default=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('function', 'module', name='unique_guilty_constraint')
    )
    op.create_table('guilty_blacklisted',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('function', sa.String(), nullable=True),
    sa.Column('module', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('records',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('architecture', sa.Text(), nullable=True),
    sa.Column('bios_version', sa.Text(), nullable=True),
    sa.Column('board_name', sa.Text(), nullable=True),
    sa.Column('build', sa.Text(), nullable=False),
    sa.Column('classification', sa.Text(), nullable=False),
    sa.Column('cpu_model', sa.Text(), nullable=True),
    sa.Column('event_id', sa.Text(), nullable=True),
    sa.Column('external', sa.Boolean(), nullable=True),
    sa.Column('host_type', sa.Text(), nullable=True),
    sa.Column('kernel_version', sa.Text(), nullable=True),
    sa.Column('machine_id', sa.Text(), nullable=True),
    sa.Column('payload_version', sa.Integer(), nullable=True),
    sa.Column('record_version', sa.Integer(), nullable=True),
    sa.Column('severity', sa.Integer(), nullable=True),
    sa.Column('system_name', sa.Text(), nullable=True),
    sa.Column('timestamp_client', sa.Numeric(), nullable=True),
    sa.Column('timestamp_server', sa.Numeric(), nullable=False),
    sa.Column('payload', sa.Text(), nullable=False),
    sa.Column('processed', sa.Boolean(), nullable=True),
    sa.Column('guilty_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['guilty_id'], ['guilty.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('records')
    op.drop_table('guilty_blacklisted')
    op.drop_table('guilty')
    # ### end Alembic commands ###
