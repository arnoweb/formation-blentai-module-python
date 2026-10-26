import os
import pytest

from uuid import uuid4
from app import app
from database import db
from models import Product, User


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client

# On fait une authentification dont on a besoin, d'où le fixture qui permet une préparation pour le test
@pytest.fixture
def auth_headers(client):

    headers_par_role = {}

    def connecter(role):
        if role in headers_par_role:
            return headers_par_role[role]

        domain = os.environ["TEST_EMAIL_DOMAIN"]
        password = os.environ[f"TEST_{role.upper()}_PASSWORD"]

        # On créé l'adresse mail unique avec uuid
        email = f"{role}-{uuid4().hex}@{domain}"

        # On créé le compte
        url = "/api/auth/register"
        print(f"Appel API : POST {url} — rôle {role}")

        response = client.post(url, json={
            "email": email,
            "password": password,
            "name": f"Test {role}"
        })

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

        response = client.post(url, json={
            "email": email,
            "password": password
        })

        assert response.status_code == 200

        token = response.get_json()["access_token"]

        headers = {"Authorization": f"Bearer {token}"}
        headers_par_role[role] = headers

        return headers

    return connecter

# On créé un produit dont on a besoin, d'où le fixture qui permet une préparation pour le test
@pytest.fixture
def produit(client, auth_headers):
    # Connexion utilisateur
    headers = auth_headers("admin")

    url = "/api/produits/"
    print(f"Appel API : POST {url}")

    response = client.post(url, headers=headers, json={
        "nom": "Clavier de test",
        "description": "Clavier sans fil",
        "categorie": "Informatique",
        "prix": 49.90,
        "quantite_stock": 10
    })

    assert response.status_code == 201

    product_id = response.get_json()["id"]

    yield {
        "id": product_id,
        "headers": headers
    }

    # On supprime le produit car c'est qu'un test
    with app.app_context():
        product = db.session.get(Product, product_id)

        if product is not None:
            db.session.delete(product)
            db.session.commit()


#####################################################
# LISTE DES PRODUITS
#####################################################

def test_liste_produits(client, produit):
    url = "/api/produits/"
    print(f"Appel API : GET {url}")

    response = client.get(url)

    assert response.status_code == 200

    products = response.get_json()

    assert isinstance(products, list)
    assert any(p["id"] == produit["id"] for p in products)


#####################################################
# DÉTAIL D'UN PRODUIT
#####################################################

def test_detail_produit(client, produit):
    url = f"/api/produits/{produit['id']}"
    print(f"Appel API : GET {url}")

    response = client.get(url)

    assert response.status_code == 200

    product = response.get_json()

    assert product["id"] == produit["id"]
    assert product["nom"] == "Clavier de test"
    assert product["description"] == "Clavier sans fil"
    assert product["categorie"] == "Informatique"
    assert product["prix"] == 49.90
    assert product["quantite_stock"] == 10


#####################################################
# CRÉATION D'UN PRODUIT
#####################################################

def test_creation_produit(produit):
    # On vérifie en BDD
    with app.app_context():
        product = db.session.get(Product, produit["id"])

        assert product is not None
        assert product.nom == "Clavier de test"
        assert product.description == "Clavier sans fil"
        assert product.categorie == "Informatique"
        assert product.prix == 49.90
        assert product.quantite_stock == 10
        assert product.date_creation is not None


#####################################################
# MODIFICATION D'UN PRODUIT
#####################################################

def test_modification_produit(client, produit):
    url = f"/api/produits/{produit['id']}"
    print(f"Appel API : {"PUT"} {url}")

    response = client.put(
        url,
        headers=produit["headers"],
        json={
            "nom": "Clavier modifié",
            "prix": 39.90,
            "quantite_stock": 5
        }
    )

    assert response.status_code == 200

    resultat = response.get_json()

    assert resultat["id"] == produit["id"]
    assert resultat["nom"] == "Clavier modifié"
    assert resultat["prix"] == 39.90

    with app.app_context():
        product = db.session.get(Product, produit["id"])

        assert product is not None
        assert product.nom == "Clavier modifié"
        assert product.prix == 39.90
        assert product.quantite_stock == 5

        # Les champs absents de la requête restent inchangés.
        assert product.categorie == "Informatique"
        assert product.description == "Clavier sans fil"


#####################################################
# SUPPRESSION D'UN PRODUIT
#####################################################

def test_suppression_produit(client, produit):
    url = f"/api/produits/{produit['id']}"
    print(f"Appel API : DELETE {url}")

    response = client.delete(url, headers=produit["headers"])

    assert response.status_code == 204

    # Vérifie la suppression réelle en base
    with app.app_context():
        assert db.session.get(Product, produit["id"]) is None

    # Le produit supprimé doit être introuvable via l'API
    response = client.get(url)

    assert response.status_code == 404


#####################################################
# ÉCRITURES REFUSÉES SANS TOKEN
#####################################################

@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_ecriture_sans_token_refusee(client, produit, method):
    url = (
        "/api/produits/"
        if method == "POST"
        else f"/api/produits/{produit['id']}"
    )

    print(f"Appel API sans token : {method} {url}")

    response = client.open(
        url,
        method=method,
        json={}
    )

    assert response.status_code == 401
