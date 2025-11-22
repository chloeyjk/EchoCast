from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta

from . import database, models, schemas, crud, auth

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI()

@app.post("/register", response_model=schemas.User)
def register(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user = auth.get_user(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db, user)

@app.post("/token", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access_token = auth.create_access_token(data={"sub": user.username},
                                            expires_delta=timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES))
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/preferences", response_model=schemas.Preference)
def add_preference(pref: schemas.PreferenceCreate, db: Session = Depends(database.get_db),
                   current_user: schemas.User = Depends(auth.get_current_user)):
    return crud.create_preference(db, current_user.id, pref)

@app.get("/preferences", response_model=list[schemas.Preference])
def get_user_preferences(db: Session = Depends(database.get_db),
                         current_user: schemas.User = Depends(auth.get_current_user)):
    return crud.get_preferences(db, current_user.id)

