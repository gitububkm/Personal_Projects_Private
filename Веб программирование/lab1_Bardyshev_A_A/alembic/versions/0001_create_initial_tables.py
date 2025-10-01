from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001_create_initial_tables'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('registered_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('is_verified_author', sa.Boolean(), nullable=False, server_default=sa.text('FALSE')),
        sa.Column('avatar_url', sa.String(length=255), nullable=True),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    op.create_table(
        'news',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('published_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('cover_image_url', sa.String(length=255), nullable=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
    )
    op.create_index('ix_news_title', 'news', ['title'], unique=False)

    op.create_table(
        'comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('text', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('news_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['news_id'], ['news.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
    )

def downgrade() -> None:
    op.drop_table('comments')
    op.drop_index('ix_news_title', table_name='news')
    op.drop_table('news')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
