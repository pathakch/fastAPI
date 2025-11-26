'''
This utils.py file is created for testing purpose only, it contains fixture which will be used in multiple test files
it also contains override_get_db and override_get_current_user which are used in testing to create testing database
and a testing user
'''

from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from sqlalchemy.orm import sessionmaker
from ..database import Base
from ..main import app
from fastapi.testclient import TestClient
from ..models import Todos, Users
from ..routers.auth import bcrypt_context
import pytest

SQLALCHEMY_DATABASE_URL = "sqlite:///./testdb.db"

engine = create_engine(url = SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread':False}, poolclass = StaticPool)
TestingSessionLocal = sessionmaker(autocommit = False, autoflush = False, bind = engine)

Base.metadata.create_all(bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        
'''
This function replace current user with below mentioned user which is having admin privileges and will help in testing endpoints
'''
def override_get_current_user():
    return {"username": 'test', "id":1, "user_role": 'admin' }

client = TestClient(app)

'''
How fixture works: 
Think of pytest fixtures as test setup factories.
You are saying:

            “Hey pytest, whenever a test needs a database record named test_todo,
            go create one for me first, give it to my test, and clean up afterward.”

pytest:
Sets up the environment
Injects the ready resource into your test
Cleans up after test finishes

                    step.1 Runs codes written till 'yield', yield(return) the object
                    step.2 wait for the function using this fixture completes
                    step.3 Runs the code below 'yield' once the test function completes.And cleans the todos table
                    so that for any other test todo table will be empty, it avoids the data mess with any test.

Note: This fixture works as dependency injection for our test functions.
'''
@pytest.fixture
def test_todo():
    todo = Todos(
        title = 'Learn To Code',
        description = 'Learn To Code Everyday',
        priority = 5,
        complete = True,
        owner_id = 1
    )

    db = TestingSessionLocal()
    db.add(todo)
    db.commit()

    yield todo

# codes below yield will run after the test function using this fixture completes, and it will teardown means close the connection
# or runs anything.
    with engine.connect() as connection:
        connection.execute(text("DELETE from todos"))
        connection.commit()


# create fixture which will create a test user for testing endpoints of user.
@pytest.fixture
def test_user():
    user = Users(
        username = "codingwithckp",
        email = "codingwithckp@email.com",
        first_name = "ckp",
        last_name = "pathak",
        hashed_password = bcrypt_context.hash("testpassword"),
        role = "admin",
        phone_number = "(111)-111-1111"
    )

    db = TestingSessionLocal()
    db.add(user)
    db.commit()

    yield user

# codes below yield will run after the test function using this fixture completes, and it will teardown means close the connection
# or runs anything.
    with engine.connect() as connection:
        connection.execute(text("DELETE from users;"))
        connection.commit()