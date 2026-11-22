import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

from app import main
from app.config import Settings, get_settings


def _settings() -> Settings:
    return Settings(
        openrouter_api_key=SecretStr("test"),
        redis_url="redis://localhost:6379/0",
        postgres_db="test",
        postgres_readonly_user="test",
        postgres_readonly_password=SecretStr("test"),
    )


@pytest.fixture
def client() -> TestClient:
    main.app.dependency_overrides[get_settings] = _settings
    return TestClient(main.app)


def test_health_ok(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    async def ok(_: Settings) -> bool:
        return True

    monkeypatch.setattr(main, "check_redis", ok)
    monkeypatch.setattr(main, "check_postgres", ok)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["checks"] == {"redis": True, "postgres": True}


def test_health_degraded_when_dependency_down(
    client: TestClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def ok(_: Settings) -> bool:
        return True

    async def down(_: Settings) -> bool:
        return False

    monkeypatch.setattr(main, "check_redis", down)
    monkeypatch.setattr(main, "check_postgres", ok)
    assert client.get("/health").status_code == 503
