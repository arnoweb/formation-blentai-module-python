import pytest
from app import app
from database import db
from models import User
from uuid import uuid4

@pytest.fixture
def client():
    # Prépare le client Flask pour les tests de ce fichier.
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_create_user(client, request):

    # On récupère le rôle passé en paramètre dans le terminal.
    role = request.config.getoption("--role")

    # Prépare les données d'inscription.
    data = {
        "email": f"{role}-{uuid4().hex}@example.com",
        "password": "MotDePasse2026!",
        "name": "Arnaud Breton",
        "role": role
    }

    # Envoie une requête POST avec ces données.
    url = "/api/auth/register"
    print(f"Appel API : POST {url}")
    response = client.post(url, json=data)

    # Vérifie la réponse provisoire de ta route.
    assert response.status_code == 201
    assert response.get_json() == {"message": "Utilisateur créé"}

    # On ouvre le context Flask pour accéder à la base.
    with app.app_context():
        # On recherche l'utilisateur en fonction de l'email transmis
        user = db.session.execute(
            db.select(User).filter_by(email=data["email"])
        ).scalar_one_or_none()

    assert user is not None

    # Cas de test de modification du compte utilisateur
    user_id = user.id
    
    data_modify = {
        "email": f"modifie-{uuid4().hex}@example.com",
        "name": "Arnaud Breton modifié"
    }

    url = f"/api/auth/register/{user_id}"
    print(f"Appel API : PUT {url}")
    response = client.put(url, json=data_modify)
    print(f"Appel API : Response {response.data}")
    assert response.status_code == 200

    # On vérifie en BDD
    with app.app_context():
        user = db.session.get(User, user_id)

        assert user is not None
        assert user.email == data_modify["email"]
        assert user.nom == data_modify["name"]


# Test de connexion d'un utilisateur

    identifiants = {
        "email": data_modify["email"],
        "password": data["password"]
    }

    url = "/api/auth/login"
    print(f"Appel API : POST {url}")

    response = client.post(url, json=identifiants)
    print(f"Appel API : Response {response.data}")

    assert response.status_code == 200



    # On récupère le token
    resultat = response.get_json()
    token = resultat.get("access_token")

    # On check s'il est vide
    assert isinstance(token, str)
    assert token != ""

    url = "/api/auth/me"
    response = client.get(url)
    print(f"Appel API : POST {url}")
    assert response.status_code == 401

    # On envoie le Bearer dans les Headers à l'appel /auth/me
    response = client.get(
        url,
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    print(f"Appel API : Response {response.data}")

    # Virification dans la BDD
    resultat = response.get_json()
    assert resultat["id"] == user_id
    assert resultat["email"] == data_modify["email"]
    assert resultat["role"] == role


#####################################################
# ÉCRITURES REFUSÉES POUR UN NON-ADMIN
#####################################################

@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_ecriture_non_admin_refusee(client, produit, auth_headers, method):
    headers = auth_headers("client")

    url = (
        "/api/produits/"
        if method == "POST"
        else f"/api/produits/{produit['id']}"
    )

    print(f"Appel API non-admin : {method} {url}")

    response = client.open(url, method=method, headers=headers, json={})

    assert response.status_code == 403