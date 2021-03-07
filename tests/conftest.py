from django.contrib.auth.models import User
from pytest import fixture, mark

from adapters import redis as redis_adapter


@fixture(scope="session")
def redis():
    redis_adapter.delete_all()

    yield

    redis_adapter.delete_all()


@fixture
@mark.django_db
def admin_user():
    return User.objects.create_user('admin', 'admin@admin.com', 'password')


@fixture
@mark.django_db
def admin_client(client, admin_user):
    response = client.post("/api/token/", data={"username": "admin", "password": "password"})

    access_token = response.json().get("access")

    client.defaults.setdefault("HTTP_AUTHORIZATION", "Bearer " + access_token)

    yield client
