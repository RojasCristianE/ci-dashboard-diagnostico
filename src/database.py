from sqlmodel import create_engine, Session, SQLModel
from .config import BASE_DIR

DB_PATH = BASE_DIR / "data" / "telemetria.sqlite"
sqlite_url = f"sqlite:///{DB_PATH}"

engine = create_engine(sqlite_url, echo=False)

def init_db():
    SQLModel.metadata.create_all(engine)

def get_session():
    return Session(engine)
