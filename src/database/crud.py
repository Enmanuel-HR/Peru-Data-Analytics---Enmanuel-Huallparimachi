from sqlalchemy.orm import Session
from .models import User, Repository

def get_user_by_login(db: Session, login: str):
    return db.query(User).filter(User.login == login).first()

def get_all_repositories(db: Session):
    return db.query(Repository).all()
