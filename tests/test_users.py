from uuid import uuid4

import pytest

from digimarket.database import db
from digimarket.models import User


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


#####################################################
# LISTE DES USERS (/auth)
#####################################################
def test_user_list_access(client, auth_headers):
    assert client.get("/api/auth/").status_code == 401
    assert client.get("/api/auth/", headers=auth_headers("client")).status_code == 403

    response = client.get("/api/auth/", headers=auth_headers("admin"))
    assert response.status_code == 200
    assert all("password_hash" not in u for u in response.get_json())

#####################################################
# SUPPRESSION
#####################################################

# Un admin peut supprimer un utilisateur, qui disparaît de la base
def test_user_delete_as_admin(app, client, auth_headers, user):
    response = client.delete(f"/api/auth/{user['id']}", headers=auth_headers("admin"))

    assert response.status_code == 204

    with app.app_context():
        assert db.session.get(User, user["id"]) is None


# Sans token 401, avec un token client 403
def test_user_delete_refused(client, auth_headers, user):
    url = f"/api/auth/{user['id']}"

    assert client.delete(url).status_code == 401
    assert client.delete(url, headers=auth_headers("client")).status_code == 403


# Supprimer un utilisateur qui n'existe pas renvoie 404
def test_user_delete_unknown_404(client, auth_headers):
    response = client.delete("/api/auth/999999", headers=auth_headers("admin"))

    assert response.status_code == 404