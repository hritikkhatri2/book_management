"""initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from app.core.roles import UserRole


# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Step 1: Create the ENUM type in PostgreSQL if it doesn't already exist
    bind = op.get_bind()
    result = bind.execute(sa.text("""
        SELECT EXISTS (
            SELECT 1
            FROM   pg_type typ
            JOIN   pg_namespace nsp ON nsp.oid = typ.typnamespace
            WHERE  typ.typname = 'userrole'
            AND    nsp.nspname = current_schema()
        );
    """)).scalar_one_or_none()

    if not result:
        op.execute("CREATE TYPE userrole AS ENUM ('CUSTOMER', 'LIBRARIAN', 'SUPERUSER');")

    # Step 2: Create user table with the role column
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('is_superuser', sa.Boolean(), nullable=True, server_default=sa.false()),
        sa.Column('google_id', sa.String(length=255), nullable=True),
        sa.Column('role', postgresql.ENUM(UserRole, name='userrole', create_type=False), nullable=False, server_default=UserRole.CUSTOMER),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('google_id')
    )
    op.create_index(op.f('ix_user_id'), 'user', ['id'], unique=False)

    # Create book table
    op.create_table(
        'book',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('author', sa.String(length=255), nullable=False),
        sa.Column('isbn', sa.String(length=13), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('publication_year', sa.Integer(), nullable=True),
        sa.Column('publisher', sa.String(length=255), nullable=True),
        sa.Column('is_available', sa.Boolean(), nullable=True, server_default=sa.true()),
        sa.Column('checked_out_at', sa.DateTime(), nullable=True),
        sa.Column('checked_out_by_id', sa.Integer(), nullable=True),
        sa.Column('due_date', sa.DateTime(), nullable=True),
        sa.Column('embedding', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['checked_out_by_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('isbn')
    )
    op.create_index(op.f('ix_book_author'), 'book', ['author'], unique=False)
    op.create_index(op.f('ix_book_id'), 'book', ['id'], unique=False)
    op.create_index(op.f('ix_book_isbn'), 'book', ['isbn'], unique=True)
    op.create_index(op.f('ix_book_title'), 'book', ['title'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_book_title'), table_name='book')
    op.drop_index(op.f('ix_book_isbn'), table_name='book')
    op.drop_index(op.f('ix_book_id'), table_name='book')
    op.drop_index(op.f('ix_book_author'), table_name='book')
    op.drop_table('book')
    op.drop_index(op.f('ix_user_id'), table_name='user')
    op.drop_table('user')

    # Drop the ENUM type using raw SQL
    op.execute("DROP TYPE IF EXISTS userrole;") 