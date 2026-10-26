import pytest

from digimarket.database import db
from digimarket.models import User
from uuid import uuid4



# On crée un utilisateur dont on a besoin, d'où le fixture qui permet une préparation pour le test
@pytest.fixture
def user(app, client):
    data = {
        "email": f"user-{uuid4().hex}@example.com",
        "password": "MotDePasse2026!",
        "name": "Arnaud Breton"
    }

    response = client.post("/api/auth/register", json=data)
    assert response.status_code == 201

    # On récupère l'id attribué par la base
    with app.app_context():
        user_db = db.session.execute(
            db.select(User).filter_by(email=data["email"])
        ).scalar_one()
        user_id = user_db.id

    return {"id": user_id, **data}


# On connecte l'utilisateur et on prépare le header avec son token
@pytest.fixture
def user_headers(client, user):
    response = client.post("/api/auth/login", json={
        "email": user["email"],
        "password": user["password"]
    })
    assert response.status_code == 200

    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


#####################################################
# INSCRIPTION
#####################################################

# L'inscription crée le compte en base, toujours avec le rôle client
def test_user_register(app, client):
    data = {
        "email": f"register-{uuid4().hex}@example.com",
        "password": "MotDePasse2026!",
        "name": "Arnaud Breton",
        "role": "admin"  # doit être ignoré par l'API
    }

    print("Appel API : POST /api/auth/register")
    response = client.post("/api/auth/register", json=data)

    assert response.status_code == 201
    assert response.get_json() == {"message": "Utilisateur créé"}

    with app.app_context():
        user_db = db.session.execute(
            db.select(User).filter_by(email=data["email"])
        ).scalar_one_or_none()

        assert user_db is not None
        assert user_db.nom == data["name"]
        assert user_db.role == "client"


#####################################################
# CONNEXION
#####################################################

# La connexion renvoie un token non vide
def test_user_login(client, user):
    print("Appel API : POST /api/auth/login")
    response = client.post("/api/auth/login", json={
        "email": user["email"],
        "password": user["password"]
    })

    assert response.status_code == 200

    token = response.get_json().get("access_token")
    assert isinstance(token, str)
    assert token != ""


#####################################################
# MODIFICATION
#####################################################

# Un utilisateur connecté peut modifier son propre compte
def test_user_update_own_account(app, client, user, user_headers):
    data_modify = {
        "email": f"modifie-{uuid4().hex}@example.com",
        "name": "Arnaud Breton modifié"
    }

    url = f"/api/auth/register/{user['id']}"
    print(f"Appel API : PUT {url}")
    response = client.put(url, json=data_modify, headers=user_headers)

    assert response.status_code == 200

    with app.app_context():
        user_db = db.session.get(User, user["id"])

        assert user_db.email == data_modify["email"]
        assert user_db.nom == data_modify["name"]


#####################################################
# PROFIL (/me)
#####################################################

# Sans token, /me doit renvoyer 401
def test_user_me_without_token_401(client):
    print("Appel API : GET /api/auth/me")
    response = client.get("/api/auth/me")

    assert response.status_code == 401


# Avec le token, /me renvoie les infos de l'utilisateur connecté
def test_user_me_with_token(client, user, user_headers):
    print("Appel API : GET /api/auth/me")
    response = client.get("/api/auth/me", headers=user_headers)

    assert response.status_code == 200

    resultat = response.get_json()
    assert resultat["id"] == user["id"]
    assert resultat["email"] == user["email"]
    assert resultat["role"] == "client"