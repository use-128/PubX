from sqlmodel import create_engine, SQLModel

# Import all models here to ensure they are registered with SQLModel's metadata
from app.models.account_model import Account
from app.models.publication_record_model import PublicationRecord


DATABASE_URL = "sqlite:///database.db"
engine = create_engine(DATABASE_URL, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)
