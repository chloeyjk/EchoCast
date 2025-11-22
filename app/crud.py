from sqlalchemy.orm import Session
from . import models, schemas, auth

def create_user(db: Session, user: schemas.UserCreate):
    hashed_pw = auth.get_password_hash(user.password)
    db_user = models.User(username=user.username, hashed_password=hashed_pw)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def create_preference(db: Session, user_id: int, pref: schemas.PreferenceCreate):
    db_pref = models.PodcastPreference(**pref.dict(), user_id=user_id)
    db.add(db_pref)
    db.commit()
    db.refresh(db_pref)
    return db_pref

def get_preferences(db: Session, user_id: int):
    return db.query(models.PodcastPreference).filter(models.PodcastPreference.user_id == user_id).all()
