from sqlmodel import SQLModel, Session, create_engine
from app.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)


def get_db():
    """Dependency to get SQLModel session"""
    with Session(engine) as session:
        yield session


def init_db():
    """Initialize database tables"""
    SQLModel.metadata.create_all(bind=engine)
