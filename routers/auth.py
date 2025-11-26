from datetime import datetime, timedelta, timezone
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from ..models import Users
from jose import jwt, JWTError
from ..database import SessionLocal 
from sqlalchemy.orm import Session
from starlette import status
from passlib.context import CryptContext # needed for hashing password
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
# 'OAuth2PasswordRequestForm' needed to get username and password from user, it's not normal fast api form, 
# it's special kind of form called OAuth to password , more secure and have it's own portal on swagger
# 'OAuth2PasswordBearer' required to decode JWT.

'''
In FastAPI router is way which gives ability to have one main.py file with it's own FastAPI app and other files like auth.py also
to have it's own FastAPI app and it's endpoints defined in auth.py file. These both app (from main.py file and from auth.py file) 
runs on same port and have endpoints from both application or say both file
'''

router = APIRouter(
    prefix = "/auth", # This will divide our auth endpoint from todos endpoint is swagger UI
    tags = ['auth']
)

'''
Below secret and algorithm will work together to add a signature to the JWT to make sure that JWT is secure and authorized
'''
SECRET_KEY = 'a20e001d5dd1b5a5c3fb64530506846e9726acad2a32658f24cc92b66876a84a' # created by running command <'openssl rand -hex 32'> in cmd terminal, 
                                                                                # this is just a unique string required to create JWT token
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes = ['bcrypt'], deprecated = 'auto')

# create dependency 
oauth2_bearer = OAuth2PasswordBearer(tokenUrl = 'auth/token') # here tokenUrl is what client will send in it's request url

# create db dependency 
def get_db():
    db = SessionLocal()
    try:
        yield db # code inside try block will executed before sending the response to user, and code inside finally block will be executed 
                 # once response delivered.This makes fastapi fast and quicker. we fetch the data from database return it to client and then 
                 # close the database after, and it's safer because we are only opening the db connecting when using it then closing it after.
    finally:
        db.close

templates = Jinja2Templates(directory = "todo/templates")

#### pages ####
@router.get("/login-page")
def render_login_page(request:Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register-page")
def render_register_page(request:Request):
    return templates.TemplateResponse("register.html", {"request": request})

### Endpoints ###
def authenticate_user(username: str, password: str, db):
    '''
    This function validates user with their username and password
    returns user if validated else False
    '''
    user = db.query(Users).filter(Users.username == username).first() # returned user is a complete object of Users class, containing all the fields of a user like, id, username, email .... etc
    if not user:
        return False
    #Below code is checking that the password sent by user and the existing password in db for that user is matching or not when user is logging in
    if not bcrypt_context.verify(password, user.hashed_password): # 'hashed_password' - exists in db , 'password'- sent by user to login.
        return False
    return user

def create_access_token(username: str, user_id: int, role : str, expires_delta: timedelta):
    '''
    This function takes username and their id which is primary key in user table in database
    and return a JWT token
    '''
    encode = {'sub':username, 'id': user_id, 'role': role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp':expires})

    return jwt.encode(encode, SECRET_KEY, algorithm = ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms= [ALGORITHM])
        username : str = payload.get('sub')
        user_id : str = payload.get('id')
        user_role : str = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code= status.HTTP_401_UNAUTHORIZED, detail = "Could Not Validate User.")
        return {'username':username, 'id':user_id, 'user_role': user_role}
    except JWTError:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = 'Could NOt Validate User')
        

# now before each request we need to be able to fetch this DB session SessionLocal and be able to open the connection and close 
# the connection on every request sent  to this FastAPI application.
db_dependency = Annotated[Session, Depends(get_db)] 

# Create a pydantic model to validate the fields sent by user to create a new user
class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    role: str
    phone_number: str

# This class is created to be used as response model in endpoint creation, please check endpoint - "/token"
class Token(BaseModel):
    access_token: str
    token_type: str

@router.post("/", status_code= status.HTTP_201_CREATED)
async def craete_user(db : db_dependency, create_user_request : CreateUserRequest):
    create_user_model = Users(  #here we can not use double ** to unpack below values and send to Users class like other books project,
        # because create_user_request is of type CreateUserRequest class and this class does not contain
        #  named hashed_password, it has password and if we send data with ** there will be mismatch with hashed_passowrd 
        # from class Users and password from class CreateUserRequest, that's why we are passing all the 
        # fields manually below
        username = create_user_request.username,
        email = create_user_request.email,
        first_name = create_user_request.first_name,
        last_name = create_user_request.last_name,
        hashed_password = bcrypt_context.hash(create_user_request.password), # a average developer would not be able to know what is this .hash() function alogorithm is 
        role = create_user_request.role,
        is_active = True,
        phone_number = create_user_request.phone_number
        
    )

    db.add(create_user_model)
    db.commit()

# Creating endpoint to receive username and password from user
# @router.post("/token")
# async def login_for_access_token(form_data : Annotated[OAuth2PasswordRequestForm, Depends()],
#                                  db : db_dependency):
    
#     user = authenticate_user(form_data.username, form_data.password, db)
#     if not user:
#         return 'Failed Authentication'
#     return 'Authentication Successful' 
# Please check enhanced version of this method below including JWT.

@router.post("/token", response_model= Token)
async def login_for_access_token(form_data : Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db : db_dependency):
    
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail = 'Could NOt Validate User')
    token = create_access_token(user.username, user.id, user.role, timedelta(minutes=20))

    return {"access_token": token, 'token_type':'bearer'}
    
    