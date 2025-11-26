from fastapi import FastAPI, APIRouter, Depends, HTTPException, Path, Query, Request, status
from starlette import status # Depends is used for dependency injection
# Dependency injection in programming means that we need to do something before we execute what we are trying to execute, 
# and that will allow us to do some kind of code behind the scenes and then inject the dependency that that function relies on
# for example: read_all functon relies on the function get_db for opening up db connection and create a session and being able to 
# then return that information back to us and then closing the session behind scenes.
# from  models import Todos
from ..models import Todos
from ..database import SessionLocal
from typing import Annotated
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from .auth import get_current_user
from starlette.responses import RedirectResponse
from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="todo/templates")

router = APIRouter(
    prefix="/todos",
    tags=["todos"]
)

# create db dependency 
def get_db():
    db = SessionLocal()
    try:
        yield db # code inside try block will executed before sending the response to user, and code inside finally block will be executed 
                 # once response delivered.This makes fastapi fast and quicker. we fetch the data from database return it to client and then 
                 # close the database after, and it's safer because we are only opening the db connecting when using it then closing it after.
    finally:
        db.close

# now before each request we need to be able to fetch this DB session SessionLocal and be able to open the connection and close 
# the connection on every request sent  to this FastAPI application.

db_dependency = Annotated[Session, Depends(get_db)] # This is the cool thing about FastAPI, we can create db dependency just using simple Annotated
user_dependency = Annotated[dict, Depends(get_current_user)]

# create pydantic model to accept request to create new todos, will include some validations for the fields 

class TodoRequest(BaseModel):

    '''
    only thing missing in below list id id, because we will not accept id for create new todo from user,
    SQLAlchemy automatically create id since it is a primary key, also user will not know that what will be id of his new todo
    and that's why id is not included here
    '''

    title : str = Field(min_length= 3)
    description : str = Field(min_length= 3, max_length= 100)
    priority : int = Field(gt= 0, lt= 6)
    complete : bool     # validation not needed either True or False

def redirect_to_login():
    redirect_response = RedirectResponse(url="/auth/login-page", status_code=status.HTTP_302_FOUND)
    redirect_response.delete_cookie(key="access_token")
    return redirect_response

### Pages ###

@router.get("/todo-page")
async def render_todo_page(request: Request, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get('access_token'))
        if user is None:
            return redirect_to_login()
        todos = db.query(Todos).filter(Todos.owner_id == user.get("id")).all()

        return templates.TemplateResponse("todo.html", {"request": request, "todos":todos, "user": user})
    except:
        return redirect_to_login()
    
@router.get('/add-todo-page')
async def render_todo_page(request: Request):
    try:
        user = await get_current_user(request.cookies.get('access_token'))

        if user is None:
            return redirect_to_login()
        return templates.TemplateResponse('add-todo.html', {"request": request, "user": user})
    except:
        return redirect_to_login()
    
@router.get("/edit-todo-page/{todo_id}")
async def render_edit_todo_page(request: Request, todo_id: int, db: db_dependency):
    try:
        user = await get_current_user(request.cookies.get("access_token"))

        if user is None:
            return redirect_to_login()
        todo = db.query(Todos).filter(Todos.id == todo_id).first()
        return templates.TemplateResponse('edit-todo.html', {"request": request, "todo":todo, "user":user})
    except:
        return redirect_to_login()


### Endpoints ###
# Create asynchronous api endpoint 
@router.get("/", status_code= status.HTTP_200_OK)
async def read_all(user : user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Authentication Failed')
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all() #this is SQLAlchemy syntax in context of ORM which will return all the object defined in Todo class.

@router.get("/todo/{todo_id}", status_code= status.HTTP_200_OK)
async def read_todo(user : user_dependency, db : db_dependency, todo_id : int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Authentication Failed')
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code= 404, detail= 'Todo Not Found')

# create post request to receive request to create new todo
@router.post("/todo", status_code= status.HTTP_201_CREATED)
async def create_todo(user : user_dependency, db: db_dependency, todo_request : TodoRequest):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Authentication Failed')
    todo_model = Todos(**todo_request.model_dump(), owner_id = user.get('id'))

    db.add(todo_model)
    db.commit()

# Create update method to update existing todo for a given todo_id
@router.put("/todo/{todo_id}", status_code= status.HTTP_204_NO_CONTENT)
async def update_todo(user : user_dependency, db : db_dependency, todo_request : TodoRequest, todo_id : int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Authentication Failed')
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if not todo_model:
        raise HTTPException(status_code= 404, detail= "Todo Not Found")
    todo_model.title = todo_request.title
    todo_model.description = todo_request.description
    todo_model.priority = todo_request.priority
    todo_model.complete = todo_request.complete

    db.add(todo_model)
    db.commit()

# create delete method to delete an existing todo for a given todo_id
@router.delete("/todo/{todo_id}", status_code= status.HTTP_204_NO_CONTENT)
async def todo_delete(user : user_dependency, db : db_dependency, todo_id : int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code = 401, detail = 'Authentication Failed')
    todo_model = db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).first()
    if not todo_model:
        raise HTTPException(status_code= 404, detail= "Todo Not Found")
    
    db.query(Todos).filter(Todos.id == todo_id).filter(Todos.owner_id == user.get('id')).delete()
    db.commit()

