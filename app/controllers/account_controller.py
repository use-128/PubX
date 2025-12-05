from sqlmodel import Session, select
from app.models.account_model import Account
from app.services.database import engine


def add_account(platform: str, username: str, password: str, remark: str = "") -> Account:
    with Session(engine) as session:
        account = Account(platform=platform, username=username, password=password, remark=remark)
        session.add(account)
        session.commit()
        session.refresh(account)
        return account


def get_all_accounts() -> list[Account]:
    with Session(engine) as session:
        statement = select(Account)
        accounts = session.exec(statement).all()
        return accounts


def update_account(account_id: int, data: dict) -> Account | None:
    with Session(engine) as session:
        account = session.get(Account, account_id)
        if account:
            for key, value in data.items():
                setattr(account, key, value)
            session.add(account)
            session.commit()
            session.refresh(account)
        return account


def delete_account(account_id: int) -> bool:
    with Session(engine) as session:
        account = session.get(Account, account_id)
        if account:
            session.delete(account)
            session.commit()
            return True
        return False

def get_account_by_id(account_id: int) -> Account | None:
    with Session(engine) as session:
        return session.get(Account, account_id)
