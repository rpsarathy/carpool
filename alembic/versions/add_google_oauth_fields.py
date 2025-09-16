"""Add Google OAuth fields to users table

Revision ID: add_google_oauth
Revises: 
Create Date: 2025-09-10 20:12:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_google_oauth'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    # First, check if we're using SQLite
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        # Check if users table exists
        inspector = sa.inspect(bind)
        tables = inspector.get_table_names()
        
        if 'users' not in tables:
            # Fresh database - create table with Google OAuth support from scratch
            op.create_table('users',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('email', sa.String(), nullable=False),
                sa.Column('password_hash', sa.String(), nullable=True),  # Nullable for Google OAuth
                sa.Column('google_id', sa.String(), nullable=True),      # New column
                sa.Column('created_at', sa.DateTime(), nullable=True),
                sa.PrimaryKeyConstraint('id')
            )
            op.create_index('ix_users_email', 'users', ['email'], unique=True)
            op.create_index('ix_users_id', 'users', ['id'], unique=False)
            op.create_index('ix_users_google_id', 'users', ['google_id'], unique=False)
        else:
            # Existing database - migrate existing table
            # First drop existing indexes to avoid conflicts
            try:
                op.drop_index('ix_users_email', table_name='users')
            except:
                pass  # Index might not exist
            try:
                op.drop_index('ix_users_id', table_name='users')
            except:
                pass  # Index might not exist
            
            # Clean up any leftover tables from previous failed migrations
            try:
                op.drop_table('users_new')
            except:
                pass  # Table might not exist
            try:
                op.drop_table('users_old')
            except:
                pass  # Table might not exist
            
            # Create new table with updated schema
            op.create_table('users_new',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('email', sa.String(), nullable=False),
                sa.Column('password_hash', sa.String(), nullable=True),  # Now nullable
                sa.Column('google_id', sa.String(), nullable=True),      # New column
                sa.Column('created_at', sa.DateTime(), nullable=True),
                sa.PrimaryKeyConstraint('id')
            )
            
            # Copy data from old table to new table
            op.execute('INSERT INTO users_new (id, email, password_hash, created_at) SELECT id, email, password_hash, created_at FROM users')
            
            # Drop old table and rename new table
            op.drop_table('users')
            op.rename_table('users_new', 'users')
            
            # Create indexes on the new table
            op.create_index('ix_users_email', 'users', ['email'], unique=True)
            op.create_index('ix_users_id', 'users', ['id'], unique=False)
            op.create_index('ix_users_google_id', 'users', ['google_id'], unique=False)
    else:
        # For PostgreSQL: use ALTER COLUMN
        op.alter_column('users', 'password_hash',
                        existing_type=sa.String(),
                        nullable=True)
        
        # Add google_id column
        op.add_column('users', sa.Column('google_id', sa.String(), nullable=True))
        op.create_index(op.f('ix_users_google_id'), 'users', ['google_id'], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == 'sqlite':
        # For SQLite: recreate table with original schema
        op.create_table('users_old',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('email', sa.String(), nullable=False),
            sa.Column('password_hash', sa.String(), nullable=False),  # Back to non-nullable
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('ix_users_email', 'users_old', ['email'], unique=True)
        op.create_index('ix_users_id', 'users_old', ['id'], unique=False)
        
        # Copy data (excluding google_id and null password_hash entries)
        op.execute('INSERT INTO users_old (id, email, password_hash, created_at) SELECT id, email, password_hash, created_at FROM users WHERE password_hash IS NOT NULL')
        
        # Drop current table and rename old table
        op.drop_table('users')
        op.rename_table('users_old', 'users')
    else:
        # For PostgreSQL
        op.drop_index(op.f('ix_users_google_id'), table_name='users')
        op.drop_column('users', 'google_id')
        
        # Make password_hash non-nullable again
        op.alter_column('users', 'password_hash',
                        existing_type=sa.String(),
                        nullable=False)
