import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import inspect, text

# Add the project root to Python's import path.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

# Load DATABASE_URL before importing application settings.
load_dotenv(PROJECT_ROOT / ".env")

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402

# Import models so SQLAlchemy registers all tables with Base.metadata.
import app.db.models  # noqa: F401, E402


def initialize_database() -> None:
    try:
        # pgvector must exist before creating the Vector(384) column.
        with engine.begin() as connection:
            connection.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector")
            )

        # Creates documents and document_chunks if they do not exist.
        Base.metadata.create_all(bind=engine)

        # Create an HNSW index for cosine-distance retrieval.
        with engine.begin() as connection:
            connection.execute(
                text(
                    """
                    CREATE INDEX IF NOT EXISTS
                    ix_document_chunks_embedding_hnsw
                    ON document_chunks
                    USING hnsw (embedding vector_cosine_ops)
                    """
                )
            )

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("Database initialized successfully.")
        print(f"Tables: {', '.join(tables)}")

        with engine.connect() as connection:
            vector_version = connection.execute(
                text(
                    """
                    SELECT extversion
                    FROM pg_extension
                    WHERE extname = 'vector'
                    """
                )
            ).scalar_one_or_none()

            indexes = connection.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE tablename = 'document_chunks'
                    ORDER BY indexname
                    """
                )
            ).scalars().all()

        print(f"pgvector version: {vector_version}")
        print(f"Document chunk indexes: {', '.join(indexes)}")

    except Exception as exc:
        print(f"Database initialization failed: {exc}")
        raise
    finally:
        engine.dispose()


if __name__ == "__main__":
    initialize_database()