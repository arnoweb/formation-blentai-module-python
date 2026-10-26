# Routes des commandes : liste, détail, création, changement de statut
from apiflask import APIBlueprint, abort
from flask_jwt_extended import jwt_required, get_jwt_identity

from digimarket.auth import admin_required
from digimarket.database import db
from digimarket.models import User, Product, Order, OrderItem
from digimarket.schemas import (
    OrderCreate, OrderStatusUpdate, OrderOut, OrderDetailOut, OrderItemListOut
)

orders_bp = APIBlueprint(
    "orders",
    __name__,
    url_prefix="/api/commandes",
    tag="Commandes"
)

# Changements de statut autorisés : une commande expédiée ou annulée est terminée
TRANSITIONS = {
    "en_attente": {"validee", "annulee"},
    "validee": {"expediee", "annulee"},
    "expediee": set(),
    "annulee": set(),
}


#####################################################
# OUTILS
#####################################################

def utilisateur_connecte():
    user = db.session.get(User, int(get_jwt_identity()))

    if user is None:
        abort(401, "Utilisateur introuvable")

    return user


def commande_accessible(commande_id):
    user = utilisateur_connecte()
    commande = db.session.get(Order, commande_id)

    # Un client ne voit que ses commandes : 404 pour ne pas révéler celles des autres
    if commande is None or (
        user.role != "admin" and commande.utilisateur_id != user.id
    ):
        abort(404, "Commande introuvable")

    return commande


#####################################################
# LISTE DES COMMANDES
#####################################################

@orders_bp.route("", methods=["GET"])
@jwt_required()
@orders_bp.output(OrderOut(many=True))
@orders_bp.doc(summary="Lister les commandes (toutes pour un admin, les siennes pour un client)",
               security="BearerAuth", responses=[401])
def get_orders():
    user = utilisateur_connecte()

    requete = db.select(Order).order_by(Order.date_commande.desc())

    # L'admin voit tout, le client uniquement son historique
    if user.role != "admin":
        requete = requete.filter_by(utilisateur_id=user.id)

    return db.session.execute(requete).scalars().all()


#####################################################
# DÉTAIL D'UNE COMMANDE
#####################################################

@orders_bp.route("/<int:commande_id>", methods=["GET"])
@jwt_required()
@orders_bp.output(OrderDetailOut)
@orders_bp.doc(summary="Détail d'une commande, avec ses lignes", security="BearerAuth", responses=[401, 404])
def get_order(commande_id):
    return commande_accessible(commande_id)


#####################################################
# LIGNES D'UNE COMMANDE
#####################################################

@orders_bp.route("/<int:commande_id>/lignes", methods=["GET"])
@jwt_required()
@orders_bp.output(OrderItemListOut(many=True))
@orders_bp.doc(summary="Lignes d'une commande", security="BearerAuth", responses=[401, 404])
def get_order_lines(commande_id):
    return commande_accessible(commande_id).lignes


#####################################################
# CRÉATION D'UNE COMMANDE
#####################################################

@orders_bp.route("", methods=["POST"])
@jwt_required()
@orders_bp.input(OrderCreate, example={
    "adresse_livraison": "12 rue des Tests, 75000 Paris",
    "lignes": [
        {"produit_id": 1, "quantite": 2},
        {"produit_id": 2, "quantite": 1}
    ]
})
@orders_bp.output(OrderDetailOut, status_code=201)
@orders_bp.doc(summary="Passer une commande", security="BearerAuth", responses=[401, 404, 409])
def create_order(json_data):
    user = utilisateur_connecte()

    # On regroupe les quantités si un même produit apparaît plusieurs fois
    quantites = {}

    for ligne in json_data["lignes"]:
        produit_id = ligne["produit_id"]
        quantites[produit_id] = quantites.get(produit_id, 0) + ligne["quantite"]

    commande = Order(
        utilisateur_id=user.id,
        adresse_livraison=json_data["adresse_livraison"],
        statut="en_attente"
    )

    for produit_id, quantite in quantites.items():
        produit = db.session.get(Product, produit_id)

        if produit is None:
            abort(404, f"Produit {produit_id} introuvable")

        # Vérification du stock à la création (le stock n'est décrémenté qu'à la validation)
        if (produit.quantite_stock or 0) < quantite:
            abort(409, f"Stock insuffisant pour {produit.nom}", detail={
                "produit_id": produit.id,
                "stock_disponible": produit.quantite_stock or 0
            })

        commande.lignes.append(OrderItem(
            produit_id=produit.id,
            quantite=quantite,
            prix_unitaire=produit.prix
        ))

    db.session.add(commande)
    db.session.commit()

    return commande


#####################################################
# ADMIN : MODIFICATION DU STATUT
#####################################################

@orders_bp.route("/<int:commande_id>", methods=["PATCH"])
@admin_required
@orders_bp.input(OrderStatusUpdate, location="query")
@orders_bp.output(OrderOut)
@orders_bp.doc(summary="Changer le statut d'une commande", security="BearerAuth",
               responses=[401, 403, 404, 409])
def update_order_status(commande_id, query_data):
    commande = db.session.get(Order, commande_id)

    if commande is None:
        abort(404, "Commande introuvable")

    nouveau_statut = query_data["statut"]
    ancien_statut = commande.statut or "en_attente"

    if nouveau_statut not in TRANSITIONS[ancien_statut]:
        abort(409, f"Impossible de passer de '{ancien_statut}' à '{nouveau_statut}'")

    # Validation : on revérifie le stock (il a pu baisser depuis la création) puis on le décrémente
    if nouveau_statut == "validee":
        for ligne in commande.lignes:
            if (ligne.produit.quantite_stock or 0) < ligne.quantite:
                abort(409, f"Stock insuffisant pour {ligne.produit.nom}", detail={
                    "produit_id": ligne.produit_id,
                    "stock_disponible": ligne.produit.quantite_stock or 0
                })

        for ligne in commande.lignes:
            ligne.produit.quantite_stock -= ligne.quantite

    # Annulation d'une commande déjà validée : on remet le stock
    if nouveau_statut == "annulee" and ancien_statut == "validee":
        for ligne in commande.lignes:
            ligne.produit.quantite_stock = (ligne.produit.quantite_stock or 0) + ligne.quantite

    commande.statut = nouveau_statut
    db.session.commit()

    return commande