import os
from uuid import uuid4

import pytest

from digimarket import create_app
from digimarket.database import db
from digimarket.models import Product, User


# L'application de test, créée une seule fois pour toute la session pytest,
# avec sa propre base SQLite dans un dossier temporaire (la vraie base n'est jamais touchée)
@pytest.fixture(scope="session")
def app(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("db") / "test.db"

    app = create_app(
        {"TESTING": True, "SQLALCHEMY_DATABASE_URI": f"sqlite:///{db_path}"}
    )

    # La base de test est vide : on crée les tables à partir des modèles
    with app.app_context():
        db.create_all()

    return app


# Client Flask de test, partagé par tous les fichiers de tests
@pytest.fixture
def client(app):
    with app.test_client() as client:
        yield client


# Pour les tests pytests - on ajoute un paramètre --role
def pytest_addoption(parser):
    parser.addoption(
        "--role", action="store", default="client", choices=["client", "admin"]
    )


# On fait une authentification dont on a besoin, d'où le fixture qui permet une préparation pour le test
@pytest.fixture
def auth_headers(app, client):

    headers_par_role = {}

    def connexion(role):
        if role in headers_par_role:
            return headers_par_role[role]

        domain = os.environ["TEST_EMAIL_DOMAIN"]
        password = os.environ[f"TEST_{role.upper()}_PASSWORD"]

        # On créé l'adresse mail unique avec uuid
        email = f"{role}-{uuid4().hex}@{domain}"

        # On créé le compte
        url = "/api/auth/register"
        print(f"Appel API : POST {url} — rôle {role}")

        response = client.post(
            url, json={"email": email, "password": password, "name": f"Test {role}"}
        )

        assert response.status_code == 201

        # On passe le compte en role admin en BDD pour pouvoir tester les fixtures produits
        # Un produit ne peut se créer qu'avec une connexion d'un utilisateur role admin
        if role == "admin":
            with app.app_context():
                user = db.session.execute(
                    db.select(User).filter_by(email=email)
                ).scalar_one()
                user.role = "admin"
                db.session.commit()

        # On Connecte l'utilisateur pour récupérer son  rôle
        url = "/api/auth/login"
        print(f"Appel API : POST {url} — rôle {role}")

        response = client.post(url, json={"email": email, "password": password})

        assert response.status_code == 200

        token = response.get_json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        headers_par_role[role] = headers

        return headers

    return connexion


# On créé un produit dont on a besoin, d'où le fixture qui permet une préparation pour le test
@pytest.fixture
def product(app, client, auth_headers):
    # Connexion utilisateur
    headers = auth_headers("admin")

    url = "/api/produits/"
    print(f"Appel API : POST {url}")

    response = client.post(
        url,
        headers=headers,
        json={
            "nom": "Clavier de test",
            "description": "Clavier sans fil",
            "categorie": "Informatique",
            "prix": 49.90,
            "quantite_stock": 10,
        },
    )

    assert response.status_code == 201

    product_id = response.get_json()["id"]

    yield {"id": product_id, "headers": headers}

    # On supprime le produit car c'est qu'un test
    with app.app_context():
        product = db.session.get(Product, product_id)

        if product is not None:
            db.session.delete(product)
            db.session.commit()
