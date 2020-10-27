import pytest


@pytest.mark.django_db
def test_api_root(client):
    response = client.get("/api/")
    
    # There is only users and groups now
    assert len(response.json().keys()) == 2