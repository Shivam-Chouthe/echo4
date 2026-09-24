from collections.abc import Generator
from sqlmodel import Session, SQLModel, create_engine
from app.core.config import settings

# SQLite database file inside backend directory
DATABASE_URL = "sqlite:///./echo.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)


def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session