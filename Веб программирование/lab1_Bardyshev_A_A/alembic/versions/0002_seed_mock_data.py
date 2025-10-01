from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '0002_seed_mock_data'
down_revision = '0001_create_initial_tables'
branch_labels = None
depends_on = None

def upgrade() -> None:
    op.execute("""
-- users
INSERT INTO users (id, name, email, is_verified_author, avatar_url)
VALUES
  ('1c0a5f8b-1111-4c3a-9f85-aaaaaaaaaaaa', 'Alice', 'alice@example.com', TRUE, 'https://pics.example/alice.png'),
  ('2d1b6e9c-2222-4d4b-8a96-bbbbbbbbbbbb', 'Bob', 'bob@example.com', FALSE, 'https://pics.example/bob.png');

-- news (by Alice)
INSERT INTO news (id, title, content, author_id, cover_image_url)
VALUES
  ('3e2c7fad-3333-4e5c-9ba7-cccccccccccc', 'Hello, FastAPI', '{"body": "JSON контент новости", "tags": ["fastapi","crud"]}', '1c0a5f8b-1111-4c3a-9f85-aaaaaaaaaaaa', 'https://pics.example/cover1.jpg');

-- comment (by Bob)
INSERT INTO comments (id, text, news_id, author_id)
VALUES
  ('4f3d80be-4444-4f6d-8cb8-dddddddddddd', 'Отличная новость!', '3e2c7fad-3333-4e5c-9ba7-cccccccccccc', '2d1b6e9c-2222-4d4b-8a96-bbbbbbbbbbbb');
    """)

def downgrade() -> None:
    op.execute("""
DELETE FROM comments WHERE id = '4f3d80be-4444-4f6d-8cb8-dddddddddddd';
DELETE FROM news WHERE id = '3e2c7fad-3333-4e5c-9ba7-cccccccccccc';
DELETE FROM users WHERE id in ('1c0a5f8b-1111-4c3a-9f85-aaaaaaaaaaaa', '2d1b6e9c-2222-4d4b-8a96-bbbbbbbbbbbb');
    """)
