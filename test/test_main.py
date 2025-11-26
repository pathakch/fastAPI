from fastapi.testclient import TestClient #The starlette.testclient module requires the httpx package to be installed.(pip install httpx)
from ..main import app
from fastapi import status

client = TestClient(app)

def test_return_health_check():
    response = client.get("/healthy")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'status' : 'Healthy'}
    