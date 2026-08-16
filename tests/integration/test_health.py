from fastapi.testclient import TestClient

from securemail.api import create_app


def test_health_endpoint_is_available_without_generation_credentials():
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_phase_00_exposes_only_the_health_endpoint():
    client = TestClient(create_app())

    assert client.get("/retrieve").status_code == 404
