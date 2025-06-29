"""Add avatar_url to User model

Revision ID: 0adf7d95e16e
Revises: 94726f174ce2
Create Date: 2025-06-15 08:03:41.305264

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0adf7d95e16e"
down_revision = "94726f174ce2"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column("avatar_url", sa.String(length=255), nullable=True)
        )

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("user", schema=None) as batch_op:
        batch_op.drop_column("avatar_url")

    # ### end Alembic commands ###
