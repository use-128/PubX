from typing import Optional
from sqlmodel import Field, SQLModel


class Account(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    platform: str = Field(index=True)
    username: str
    password: str
    remark: Optional[str] = None
