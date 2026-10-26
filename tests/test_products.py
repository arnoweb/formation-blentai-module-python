import pytest

from digimarket.database import db
from digimarket.models import Product


#####################################################
# LISTE DES PRODUITS
#####################################################

def test_products_list(client, product):
    url = "/api/produits/"
    print(f"Appel API : GET {url}")

    response = client.get(url)

    assert response.status_code == 200

    body = response.get_json()

    assert isinstance(body["products"], list)
    assert any(p["id"] == product["id"] for p in body["products"])
    assert body["pagination"]["page"] == 1

# Les filtres de la liste : catégorie, recherche dans le nom, prix
def test_products_list_filters(client, product):
    url = "/api/produits/"

    trouve = client.get(url, query_string={"categorie": "Informatique", "nom": "clav", "prix_max": 50}).get_json()
    assert any(p["id"] == product["id"] for p in trouve["products"])

    absent = client.get(url, query_string={"prix_min": 100}).get_json()
    assert all(p["id"] != product["id"] for p in absent["products"])


# per_page limite le nombre de produits renvoyés, et une valeur trop grande est refusée
def test_products_list_pagination(client, product):
    body = client.get("/api/produits/", query_string={"per_page": 1}).get_json()

    assert len(body["products"]) <= 1
    assert body["pagination"]["per_page"] == 1

    assert client.get("/api/produits/", query_string={"per_page": 1000}).status_code == 400

#####################################################
# DÉTAIL D'UN PRODUIT
#####################################################

def test_product_detail(client, product):
    url = f"/api/produits/{product['id']}"
    print(f"Appel API : GET {url}")

    response = client.get(url)

    assert response.status_code == 200

    product = response.get_json()

    assert product["id"] == product["id"]
    assert product["nom"] == "Clavier de test"
    assert product["description"] == "Clavier sans fil"
    assert product["categorie"] == "Informatique"
    assert product["prix"] == 49.90
    assert product["quantite_stock"] == 10


#####################################################
# CRÉATION D'UN PRODUIT
#####################################################

def test_product_create(app, product):
    # On vérifie en BDD
    with app.app_context():
        product = db.session.get(Product, product["id"])

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

def test_product_modify(app, client, product):
    url = f"/api/produits/{product['id']}"
    print(f"Appel API : {"PUT"} {url}")

    response = client.put(
        url,
        headers=product["headers"],
        json={
            "nom": "Clavier modifié",
            "prix": 39.90,
            "quantite_stock": 5
        }
    )

    assert response.status_code == 200

    resultat = response.get_json()

    assert resultat["id"] == product["id"]
    assert resultat["nom"] == "Clavier modifié"
    assert resultat["prix"] == 39.90

    with app.app_context():
        product = db.session.get(Product, product["id"])

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

def test_product_delete(app, client, product):
    url = f"/api/produits/{product['id']}"
    print(f"Appel API : DELETE {url}")

    response = client.delete(url, headers=product["headers"])

    assert response.status_code == 204

    # Vérifie la suppression réelle en base
    with app.app_context():
        assert db.session.get(Product, product["id"]) is None

    # Le produit supprimé doit être introuvable via l'API
    response = client.get(url)

    assert response.status_code == 404


#####################################################
# ÉCRITURES REFUSÉES SANS TOKEN
#####################################################
# Utilisateur non connecté
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_product_protection(client, product, method):
    url = (
        "/api/produits/"
        if method == "POST"
        else f"/api/produits/{product['id']}"
    )

    print(f"Appel API sans token : {method} {url}")

    response = client.open(
        url,
        method=method,
        json={}
    )

    assert response.status_code == 401


#####################################################
# ÉCRITURES REFUSÉES POUR UN NON-ADMIN
#####################################################
#Utilisateur connecté mais n'a pas le role admin
@pytest.mark.parametrize("method", ["POST", "PUT", "DELETE"])
def test_create_delete_for_nonadmin(client, product, auth_headers, method):
    headers = auth_headers("client")

    url = (
        "/api/produits/"
        if method == "POST"
        else f"/api/produits/{product['id']}"
    )

    print(f"Appel API non-admin : {method} {url}")

    response = client.open(url, method=method, headers=headers, json={})

    assert response.status_code == 403