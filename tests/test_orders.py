import pytest

from digimarket.database import db
from digimarket.models import Order


# On crée une commande dont on a besoin, d'où le fixture qui permet une préparation pour le test
@pytest.fixture
def order(app, client, auth_headers, product):
    # Une commande est passée par un client (l'admin sert seulement à créer le produit)
    headers = auth_headers("client")

    url = "/api/commandes"
    print(f"Appel API : POST {url}")

    response = client.post(url, headers=headers, json={
        "adresse_livraison": "12 rue des Tests, 75000 Paris",
        "lignes": [
            {"produit_id": product["id"], "quantite": 2}
        ]
    })

    assert response.status_code == 201

    order_id = response.get_json()["id"]

    yield {
        "id": order_id,
        "headers": headers,                   # token du client qui a passé la commande
        "admin_headers": product["headers"],  # token admin, pour changer le statut
        "product_id": product["id"],
        "quantite": 2
    }

    # On supprime la commande car c'est qu'un test (les lignes partent avec, grâce au cascade)
    with app.app_context():
        order = db.session.get(Order, order_id)

        if order is not None:
            db.session.delete(order)
            db.session.commit()


#####################################################
# CRÉATION ET LECTURE
#####################################################

# Le client retrouve sa commande avec ses lignes et le bon total
def test_order_detail(client, order):
    response = client.get(f"/api/commandes/{order['id']}", headers=order["headers"])

    assert response.status_code == 200

    commande = response.get_json()
    assert commande["statut"] == "en_attente"
    assert commande["lignes"][0]["produit_id"] == order["product_id"]
    assert commande["lignes"][0]["quantite"] == order["quantite"]
    assert commande["total"] == round(order["quantite"] * 49.90, 2)


# Sans token, la liste des commandes doit renvoyer 401
def test_order_list_without_token_401(client):
    response = client.get("/api/commandes")

    assert response.status_code == 401


#####################################################
# STOCK
#####################################################

# On ne peut pas commander plus que le stock disponible
def test_order_insufficient_stock_409(client, auth_headers, product):
    response = client.post("/api/commandes", headers=auth_headers("client"), json={
        "adresse_livraison": "12 rue des Tests, 75000 Paris",
        "lignes": [{"produit_id": product["id"], "quantite": 999}]
    })

    assert response.status_code == 409


# La validation décrémente le stock, l'annulation le remet
def test_order_validate_then_cancel_restores_stock(client, order):
    url = f"/api/commandes/{order['id']}"
    url_produit = f"/api/produits/{order['product_id']}"

    stock_initial = client.get(url_produit).get_json()["quantite_stock"]

    response = client.patch(url, headers=order["admin_headers"], query_string={"statut": "validee"})
    assert response.status_code == 200
    assert client.get(url_produit).get_json()["quantite_stock"] == stock_initial - order["quantite"]

    response = client.patch(url, headers=order["admin_headers"], query_string={"statut": "annulee"})
    assert response.status_code == 200
    assert client.get(url_produit).get_json()["quantite_stock"] == stock_initial


#####################################################
# STATUTS
#####################################################

# Une commande annulée ne peut plus changer de statut
def test_order_invalid_transition_409(client, order):
    url = f"/api/commandes/{order['id']}"

    client.patch(url, headers=order["admin_headers"], query_string={"statut": "annulee"})
    response = client.patch(url, headers=order["admin_headers"], query_string={"statut": "validee"})

    assert response.status_code == 409


# Un client ne peut pas changer le statut de sa propre commande
def test_order_status_as_client_403(client, order):
    response = client.patch(
        f"/api/commandes/{order['id']}",
        headers=order["headers"],
        query_string={"statut": "validee"}
    )

    assert response.status_code == 403

#####################################################
# UN USER AVEC COMMANDES NE PEUT PAS ETRE DELETE
#####################################################
def test_user_with_orders_cannot_be_deleted_409(client, order):
    commande = client.get(f"/api/commandes/{order['id']}", headers=order["headers"]).get_json()

    response = client.delete(
        f"/api/auth/{commande['utilisateur_id']}",
        headers=order["admin_headers"]
    )

    assert response.status_code == 409