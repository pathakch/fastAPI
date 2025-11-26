from fastapi import FastAPI, Request, status
from .models import Base
from .database import engine, SessionLocal
from .routers import auth, todos, admin, user
# commenting out below import of jinja2, because we will use redirectresponse so jinja2 is not required, we will change below
#'templates' variable and function endpoint also
# from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

# this below line will not automatically be ran if we change anything in our model.py, since we have defined table in model.py,
# so we need to delete the database file 'todos.db' in this folder and then run this below line to create new db file everytime model.py changes.
# further we will see how to enhance db without deleting the db file everytime using Alembic in coming lectures.
Base.metadata.create_all(bind = engine)


'''
For frontend we need two installations 1. aiofiles 2. jinja2
'''
# not using jinja2 so commenting out, using redirectresponse instead.
# templates = Jinja2Templates(directory = "todo/templates") #this todo/templates is the directory where our todoapp html files is going to live

app = FastAPI()

app.mount("/static", StaticFiles(directory="todo/static"), name = "static")


# Below endpoint is created which will allow to open up this html file
@app.get("/")
def test(request : Request):
    # return templates.TemplateResponse("home.html", {"request": request})
    return RedirectResponse(url="/todos/todo-page", status_code=status.HTTP_302_FOUND)

@app.get("/healthy")
def health_check():
    return {"status": "Healthy"}

app.include_router(auth.router)
app.include_router(todos.router)
app.include_router(admin.router)
app.include_router(user.router)
