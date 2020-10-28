import pytest


@pytest.mark.django_db
def test_simple_login_auth(client, admin_user):
    assert client.login(username="admin", password="password")


@pytest.mark.django_db
def test_jwt_token_retrieval(client, admin_user):
    response = client.post("/api/token/", data={"username": "admin", "password": "password"})

    assert response.status_code == 200

    tokens = response.json()

    assert tokens.get("access")
    assert tokens.get("refresh")


@pytest.mark.django_db
def test_jwt_token_refresh(client, admin_user):
    response = client.post("/api/token/", data={"username": "admin", "password": "password"})

    tokens = response.json()

    access_token = tokens.get("access")
    refresh_token = tokens.get("refresh")

    response = client.post("/api/token/refresh/", data={"refresh": refresh_token})

    assert response.status_code == 200

    assert access_token != response.json().get("access")


@pytest.mark.django_db
def test_auth_through_jwt_header(client, admin_user):
    response = client.post("/api/token/", data={"username": "admin", "password": "password"})

    tokens = response.json()

    access_token = tokens.get("access")

    response = client.get("/api/", HTTP_AUTHORIZATION="Bearer " + access_token)

    assert response.status_code == 200
