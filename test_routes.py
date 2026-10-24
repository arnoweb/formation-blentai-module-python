import pytest
from app import app # on importe l'application Flask

# on crée un fixture pour le client de test
@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

# on déclare le paramètre url pour les tests
@pytest.mark.parametrize("url", ["/", "/users/", "/admin/"])

# on teste les routes GET et on vérifie que le status code est 200
def test_routes_get_retournent_200(client, url):
    response = client.get(url)
    assert response.status_code == 200

# Seules ces deux routes acceptent POST.
# Les fonctions Flask correspondantes doivent retourner le statut 201.
@pytest.mark.parametrize("url", ["/users/", "/admin/"])
def test_routes_post_retournent_201(client, url):
    response = client.post(url)
    assert response.status_code == 201


# Les routes PUT attendent un identifiant dans l'URL.
@pytest.mark.parametrize("url", ["/users/1", "/admin/1"])
def test_routes_put_retournent_200(client, url):
    response = client.put(url)
    assert response.status_code == 200