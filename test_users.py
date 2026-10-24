import pytest
from app import app


@pytest.fixture
def client():
    # Prépare le client Flask pour les tests de ce fichier.
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_create_user(client):
    # Prépare les données d'inscription.
    data = {
        "email": "arnbret@gemail.com",
        "password": "MotDePasse2026!",
        "name": "Arnaud Breton"
    }

    # Envoie une requête POST avec ces données.
    response = client.post("/users/", json=data)

    # Vérifie la réponse provisoire de ta route.
    assert response.status_code == 201
    assert response.get_json() == {"message": "Utilisateur créé"}