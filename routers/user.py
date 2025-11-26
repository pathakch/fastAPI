from fastapi import FastAPI, APIRouter, Depends, HTTPException, Path, Query
from starlette import status
from ..models import Users
from ..database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from .auth import get_current_user
from passlib.context import CryptContext

router = APIRouter(
    prefix = "/user", 
    tags = ['user']
)

# create db dependency 
def get_db():
    db = SessionLocal()
    try:
        yield db 
    finally:
        db.close

db_dependency = Annotated[Session, Depends(get_db)] 
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes = ['bcrypt'], deprecated = 'auto')

# create a pydantic model to validate the new password(provided by user) while changing the old password
class UserVerification(BaseModel):
    password : str
    new_password : str =Field(min_length=6)

# create user endpoint to get all the information for the user
@router.get("/", status_code=status.HTTP_200_OK)
async def read_all(user : user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail = "Authentication Failed")
    todo_model = db.query(Users).filter(Users.id == user.get('id')).first()
    if todo_model is None:
        raise HTTPException(status_code=404, detail = "User Not Found")
    return todo_model

#create endpoint to change password of a user
@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(user : user_dependency, db : db_dependency, user_verification : UserVerification):
    if user is None:
        raise HTTPException(status_code=401, detail = "Authentication Failed")
    user_model = db.query(Users).filter(Users.id == user.get('id')).first()
    
    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(status_code=401, detail = "Error on Password change")
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()

# create endpoint to add phone number
@router.put("/phonenumber/{phone_number}", status_code=status.HTTP_204_NO_CONTENT)
async def update_phone_number(user : user_dependency, db : db_dependency, phone_number : str):
     if user is None:
         raise HTTPException(status_code = 401, detail = 'Authentication Failed')
     user_model = db.query(Users).filter(Users.id == user.get('id')).first()
     user_model.phone_number = phone_number
     
     db.add(user_model)
     db.commit()
