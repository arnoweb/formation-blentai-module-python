import pytest
from app import app # on importe l'application Flask

# on crée un fixture pour le client de test
@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

# on déclare le paramètre url pour les tests
@pytest.mark.parametrize("url", ["/", "/api/auth/"])

# on teste les routes GET et on vérifie que le status code est 200
def test_routes_get_retournent_200(client, url):
    response = client.get(url)
    assert response.status_code == 200