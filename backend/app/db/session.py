from collections.abc import Generator
from sqlalchemy import text
from sqlmodel import Session, SQLModel, create_engine
from app.core.config import settings

DATABASE_URL = "sqlite:///./echo.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db() -> None:
    # 1. Create tables if they don't exist
    SQLModel.metadata.create_all(engine)

    # 2. Migration safety check for existing SQLite databases:
    # If the database was created when category was NOT NULL, SQLite doesn't alter constraints automatically.
    with engine.connect() as conn:
        # Check table info for memories
        result = conn.execute(text("PRAGMA table_info(memories);")).fetchall()
        if result:
            # Columns that must be nullable in the PENDING state:
            # PRAGMA row format: (cid, name, type, notnull, dflt_value, pk)
            columns_to_check = {"category", "title", "summary", "intent"}
            needs_rebuild = any(
                row[1] in columns_to_check and row[3] == 1 for row in result
            )
            if needs_rebuild:
                # Recreate table cleanly so existing dev DBs automatically match the new schema
                conn.execute(text("ALTER TABLE memories RENAME TO memories_old;"))
                SQLModel.metadata.create_all(engine)
                # Copy existing data over
                conn.execute(
                    text(
                        """
                        INSERT INTO memories (id, client_id, raw_content, source_url, source_type, client_timestamp, category, title, summary, intent, keywords_json, target_place_json, status, created_at)
                        SELECT id, client_id, raw_content, source_url, source_type, client_timestamp, category, title, summary, intent, keywords_json, target_place_json, status, created_at
                        FROM memories_old;
                        """
                    )
                )
                conn.execute(text("DROP TABLE memories_old;"))
                conn.commit()


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session