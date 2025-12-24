from sqlmodel import Session
from app.models.publication_record_model import PublicationRecord
from app.services.database import engine


def add_publication_record(
    account_id: int,
    title: str,
    description: str,
    media_paths: list[str],
    status: str,
) -> PublicationRecord:
    """
    Adds a new publication record to the database.
    """
    with Session(engine) as session:
        # Convert list of paths to a single string
        media_paths_str = ";".join(media_paths)
        
        record = PublicationRecord(
            account_id=account_id,
            title=title,
            description=description,
            media_paths=media_paths_str,
            status=status,
        )
        session.add(record)
        session.commit()
        session.refresh(record)
        return record
