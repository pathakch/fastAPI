from .utils import *
from ..routers.auth import get_db, authenticate_user, SECRET_KEY, ALGORITHM, create_access_token, get_current_user
from jose import jwt
from datetime import timedelta
import pytest
from fastapi import HTTPException

app.dependency_overrides[get_db] = override_get_db


def test_authenticate_user(test_user):
    db = TestingSessionLocal()

    authenticated_user = authenticate_user(test_user.username, "testpassword", db)

    assert authenticated_user is not None
    assert authenticated_user.username == test_user.username

    # test with a nonexisting user(user who is not existing in db)
    non_existing_user = authenticate_user("wrong_username", "testpassword", db)
    assert non_existing_user is False

    # test to validate a user who is loging in with a wrong password
    wrong_password_user = authenticate_user(test_user.username, "wronpassword", db)
    assert wrong_password_user is False

def test_create_secret_access_token_success():
    username = "testuser"
    user_id = 1
    role = 'user'
    expires = timedelta(days = 1)

    token = create_access_token(username, user_id, role, expires)

    decoded_token = jwt.decode(token, SECRET_KEY, algorithms = [ALGORITHM],
                               options = {"verify_signature":False})
    
    assert decoded_token['sub'] == username
    assert decoded_token['id'] == user_id
    assert decoded_token['role'] == role


'''
asyncio is installed to test async function 'get_current_user', this library 'asyncio' is not included in pytest by default 
which is required to test async functionality <pip install pytest-asyncio>
'''
@pytest.mark.asyncio 
async def test_get_current_user_valid_token():
    encode = {'sub': 'testuser', 'id': 1, 'role': 'admin'}

    token = jwt.encode(encode, SECRET_KEY, algorithm = ALGORITHM)

    user = await get_current_user(token)
    assert user == {'username':'testuser', 'id': 1, 'user_role':'admin'}

@pytest.mark.asyncio
async def test_get_current_user_missing_payload():
    encode = {"role": "user"}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == 'Could Not Validate User.'
