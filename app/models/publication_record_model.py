from typing import Optional, List
from sqlmodel import Field, SQLModel, Relationship
from datetime import datetime
from .account_model import Account


class PublicationRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: str
    media_paths: str  # Storing as a semicolon-separated string
    status: str = Field(index=True) # e.g., "success", "failed"
    published_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    
    account_id: Optional[int] = Field(default=None, foreign_key="account.id")
    # This is a forward reference, so it's a string.
    # At runtime, SQLModel will resolve this to the Account class.
    account: Optional["Account"] = Relationship(back_populates="publication_records")
