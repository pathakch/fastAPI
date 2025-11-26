from .utils import *
from fastapi import status
from ..routers.user import get_db, get_current_user

app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_return_user(test_user):
    response = client.get("/user")
    assert response.status_code == status.HTTP_200_OK

    # here we can not write response.json() because response json will return hashed password string , which will not match if we put correct unhashed password
    # so we will compare all other fields of user like username,email,first_name last_name etc excluding password.
    assert response.json()["username"] == "codingwithckp" 
    assert response.json()["email"] == "codingwithckp@email.com"
    assert response.json()["first_name"] == "ckp"
    assert response.json()["last_name"] == "pathak"
    assert response.json()["role"] == "admin"
    assert response.json()["phone_number"] == "(111)-111-1111"

def test_change_Password_success(test_user):
    response = client.put("/user/password", json = {"password":"testpassword", "new_password":"newpassword"})
    assert response.status_code == 204

def test_change_password_invalid_current_password(test_user):
    response = client.put("/user/password", json = {"password":"wrongpassword", "new_password":"newpassword"})

    assert response.status_code == 401
    assert response.json() == {"detail":"Error on Password change"}

def test_phone_number_change_success(test_user):
    response = client.put("/user/phonenumber/(123)-123-1234")

    assert response.status_code == status.HTTP_204_NO_CONTENT