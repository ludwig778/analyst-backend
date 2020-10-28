import pytest


@pytest.mark.django_db
def test_api_root(admin_client, admin_user):
    response = admin_client.get("/api/")

    assert len(response.json().keys()) == 2
