import pytest
from app import app # on importe l'application Flask

# on crée un fixture pour le client de test
@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

# on déclare le paramètre url pour les tests
# on teste les routes GET et on vérifie que le status code est 200
@pytest.mark.parametrize("url", ["/", "/api/auth/","/api/produits/"])
def test_routes_get(client, url):
    response = client.get(url)
    assert response.status_code == 200

# on teste que la route commandes n'est pas accessible depuis l'exterieur
def test_routes_get_unauthorized(client):
    response = client.get("/api/commandes")
    assert response.status_code == 401