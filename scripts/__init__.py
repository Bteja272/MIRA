import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, inspect, text

# Allow imports such as "from app.db..."
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# Import all model classes so SQLAlchemy registers their tables.
from app.db.base import Base  
import app.db.models  


def initialize_database() -> None:
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is missing. Add it to the local .env file."
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    try:
        # Ensure pgvector is enabled.
        with engine.begin() as connection:
            connection.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector")
            )

        # Create every table defined by the SQLAlchemy models.
        Base.metadata.create_all(bind=engine)

        inspector = inspect(engine)
        tables = inspector.get_table_names()

        print("Database initialized successfully.")
        print(f"Database: {database_url.rsplit('@', 1)[-1]}")
        print(f"Tables: {', '.join(tables) if tables else 'No tables found'}")

    finally:
        engine.dispose()


if __name__ == "__main__":
    initialize_database()