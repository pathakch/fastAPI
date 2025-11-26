from ..routers.todos import get_db, get_current_user
from fastapi import status
from ..models import Todos
from .utils import *

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

# This function will test all the todos for a user, so it's return type will be a list of dictionary(json string)
def test_read_all_authenticated(test_todo):
    respone = client.get("/todos")
    assert respone.status_code == status.HTTP_200_OK
    assert respone.json() == [{
        'title':'Learn To Code', 
        'description':'Learn To Code Everyday', 
        'priority':5, 'complete':True, 'owner_id':1, 'id':1}] # return type is list of json string

# This function will test one todo for a specific todo_id, here todo_id is 1 which is client requesting.
def test_read_authenticated(test_todo):
    respone = client.get("/todos/todo/1")
    assert respone.status_code == status.HTTP_200_OK
    assert respone.json() == {
        'title':'Learn To Code', 
        'description':'Learn To Code Everyday', 
        'priority':5, 'complete':True, 
        'owner_id':1, 'id':1} # return type is just one json string(return is todo for one todo_id)

# This function will test the todo which is not existing in database
def test_read_one_authenticated_not_found():
    response = client.get("/todos/todo/999")
    assert response.status_code == 404
    assert response.json() == {'detail': 'Todo Not Found'}

# Why fixture 'test_todo' is required in below testing, because it will delete all the data from todo table once test is complete
# deleting logic is written in fixture and thats why fixture is required here, otherwise below test function would run without this fixture
# also but in that case the new todo which this test will create will not be deleted, But 
# we want to run every test with a fresh data , also each test should clean it's own mess after test completed and that's why 
# test_todo fixture required
def test_create_todo(test_todo):
    todo_request = {
        "title":'New Todo',
        "description": 'A new Todo to test',
        "priority": 5,
        "complete": False
    }

    response = client.post("/todos/todo/", json=todo_request)
    assert response.status_code == 201

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 2).first() # here id == 2 because , one todo will be created by fixture 'test_todo' and 
                                                            # other todo we are creating for this test, so total 2 todos will be there in Todos table.
    assert model.title == todo_request.get("title")
    assert model.description == todo_request.get("description")
    assert model.priority == todo_request.get("priority")
    assert model.complete == todo_request.get("complete")

# This test function tests update todo endpoint, when we fixture 'test_todo' it will create one todo, and we will try to update
# that existing todo.
def test_update_todo(test_todo):
    update_request = {
        "title": "Change the title of the todo already saved",
        "description": "Need to learn Everyay!",
        "priority": 5,
        "complete": False
    }

    response = client.put("/todos/todo/1", json = update_request)
    assert response.status_code == 204

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()
    
    assert model.title == update_request.get("title")
    assert model.description == update_request.get("description")
    assert model.priority == update_request.get("priority")
    assert model.complete == update_request.get("complete")

# This function tests update endpoint for the todo_id which does not exist in todo table or in db.
def test_update_todo_not_exist():
    update_request = {
        "title": "Change the title of the todo already saved",
        "description": "Need to Learn Everyday!",
        "priority": 5,
        "complete": False
    }

    response = client.put("/todos/todo/999", json=update_request) # todo_id 999 does not exist in db
    assert response.status_code == 404
    assert response.json() == {"detail": "Todo Not Found"}

# This function tests delete endpoint, it will delete a todo with a todo_id (created by fixture 'test_todo')
def test_delete_todo(test_todo):
    response = client.delete("/todos/todo/1")

    assert response.status_code == 204

    db = TestingSessionLocal()
    model = db.query(Todos).filter(Todos.id == 1).first()

    assert model is None

# This test function will test delete endpoint if todo_id does not exist, meaning todo not found
def test_delete_todo_not_found():
    response = client.delete("/todos/todo/999")

    assert response.status_code == 404
    assert response.json() == {"detail":"Todo Not Found"}

