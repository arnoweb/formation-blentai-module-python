from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import User, Product, Order, OrderItem, STATUTS_COMMANDE
from products import admin_required

orders_bp = Blueprint(
    "orders",
    __name__,
    url_prefix="/api/commandes"
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
    return db.session.get(User, int(get_jwt_identity()))

# On transforme l'objet en dictionnaire 
# Dans l'API on retourne du JSON via jsonify
# Et jsonify ne sait pas convertir un objet SQLAlechemy
# Avantage : si un champ change dans la base, la donnée renvoyée dans l'API est la même
def ligne_en_dict(ligne):
    return {
        "id": ligne.id,
        "produit_id": ligne.produit_id,
        "produit_nom": ligne.produit.nom if ligne.produit else None,
        "quantite": ligne.quantite,
        "prix_unitaire": ligne.prix_unitaire,
        "sous_total": round(ligne.quantite * ligne.prix_unitaire, 2)
    }

# Affichage ou non des produits de chaque commande
# La liste de commandes peut être avec ou sans la liste des produits commandés
def commande_en_dict(commande, avec_lignes=False):
    resultat = {
        "id": commande.id,
        "utilisateur_id": commande.utilisateur_id,
        "date_commande": (
            commande.date_commande.isoformat()
            if commande.date_commande else None
        ),
        "adresse_livraison": commande.adresse_livraison,
        "statut": commande.statut,
        "total": commande.total
    }
    # Detail de la commande
    if avec_lignes:
        resultat["lignes"] = [ligne_en_dict(ligne) for ligne in commande.lignes]

    return resultat


def commande_accessible(commande_id):

    user = utilisateur_connecte()

    if user is None:
        return None, (jsonify({"error": "Utilisateur introuvable"}), 401)

    commande = db.session.get(Order, commande_id)

    # Commandes visibles que pour l'utilisateur connecté ou l'admin (qui voit tout)
    if commande is None or (
        user.role != "admin" and commande.utilisateur_id != user.id
    ):
        return None, (jsonify({"error": "Commande introuvable"}), 404)

    return user, commande


#####################################################
# LISTE DES COMMANDES
#####################################################

@orders_bp.route("", methods=["GET"])
@jwt_required()
def get_orders():
    user = utilisateur_connecte()

    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 401

    requete = db.select(Order).order_by(Order.date_commande.desc())

    # L'admin voit tout, le client uniquement son historique
    if user.role != "admin":
        requete = requete.filter_by(utilisateur_id=user.id)

    commandes = db.session.execute(requete).scalars().all()

    return jsonify([commande_en_dict(c) for c in commandes]), 200


#####################################################
# DÉTAIL D'UNE COMMANDE
#####################################################

@orders_bp.route("/<int:commande_id>", methods=["GET"])
@jwt_required()
def get_order(commande_id):
    user, commande = commande_accessible(commande_id)

    if user is None:
        return commande

    return jsonify(commande_en_dict(commande, avec_lignes=True)), 200


#####################################################
# LIGNES D'UNE COMMANDE
#####################################################

@orders_bp.route("/<int:commande_id>/lignes", methods=["GET"])
@jwt_required()
def get_order_lines(commande_id):
    user, commande = commande_accessible(commande_id)

    if user is None:
        return commande

    return jsonify([ligne_en_dict(ligne) for ligne in commande.lignes]), 200


#####################################################
# CRÉATION D'UNE COMMANDE
#####################################################

@orders_bp.route("", methods=["POST"])
@jwt_required()
def create_order():
    user = utilisateur_connecte()

    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 401

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({"error": "Un objet JSON est attendu"}), 400

    adresse = data.get("adresse_livraison")

    if not isinstance(adresse, str) or not adresse.strip():
        return jsonify({"error": "Adresse de livraison requise"}), 400

    lignes = data.get("lignes")

    if not isinstance(lignes, list) or not lignes:
        return jsonify({"error": "La commande doit contenir au moins un produit"}), 400

    # Regroupement des quantites du même produit d'une commande
    quantites = {}

    # Exemple d'entrée :
    #   "lignes": [
    #       { "produit_id": 4, "quantite": 2 },
    #       { "produit_id": 7, "quantite": 1 },
    #       { "produit_id": 4, "quantite": 3 }
    #   ]
    for ligne in lignes:
        # Vérification que c'est un objet JSON
        # C'est la technique de la clause de garde (plutôt que if else)
        if not isinstance(ligne, dict):
            return jsonify({"error": "Ligne de commande invalide"}), 400

        produit_id = ligne.get("produit_id")
        quantite = ligne.get("quantite")

        # On check si produit, quantite est un entier
        # On check si produit, quantite n'est pas un boolean
        # Ce 2ème check est nécessaire car un Bolean True, False est un entier déguisé
        if (
            not isinstance(produit_id, int) or isinstance(produit_id, bool)
            or not isinstance(quantite, int) or isinstance(quantite, bool)
            or quantite <= 0
        ):
            return jsonify({
                "error": "Chaque ligne doit avoir un produit_id et une quantite entière positive"
            }), 400

        quantites[produit_id] = quantites.get(produit_id, 0) + quantite

    commande = Order(
        utilisateur_id=user.id,
        adresse_livraison=adresse.strip(),
        statut="en_attente"
    )

    for produit_id, quantite in quantites.items():
        produit = db.session.get(Product, produit_id)

        if produit is None:
            return jsonify({"error": f"Produit {produit_id} introuvable"}), 404

        # Vérification du stock à la création
        # le stock n'est décrémenté qu'à la validation
        if (produit.quantite_stock or 0) < quantite:
            return jsonify({
                "error": f"Stock insuffisant pour {produit.nom}",
                "produit_id": produit.id,
                "stock_disponible": produit.quantite_stock or 0
            }), 409

        commande.lignes.append(OrderItem(
            produit_id=produit.id,
            quantite=quantite,
            prix_unitaire=produit.prix
        ))

    db.session.add(commande)
    db.session.commit()

    return jsonify({
        "message": "Commande créée",
        "commande": commande_en_dict(commande, avec_lignes=True)
    }), 201


#####################################################
# ADMIN : MODIFICATION DU STATUT
#####################################################
@orders_bp.route("/<int:commande_id>", methods=["PATCH"])
@admin_required
def update_order_status(commande_id):
    commande = db.session.get(Order, commande_id)

    if commande is None:
        return jsonify({"error": "Commande introuvable"}), 404

    data = request.get_json(silent=True)
    # Ternaire
    nouveau_statut = data.get("statut") if isinstance(data, dict) else None

    if nouveau_statut not in STATUTS_COMMANDE:
        return jsonify({
            "error": "Statut invalide",
            "statuts_possibles": list(STATUTS_COMMANDE)
        }), 400

    ancien_statut = commande.statut or "en_attente"

    if nouveau_statut not in TRANSITIONS[ancien_statut]:
        return jsonify({
            "error": f"Impossible de passer de '{ancien_statut}' à '{nouveau_statut}'"
        }), 409

    # Validation : on revérifie le stock qui a pu baisser depuis la création
    #  puis on le décrémente
    if nouveau_statut == "validee":
        for ligne in commande.lignes:
            if (ligne.produit.quantite_stock or 0) < ligne.quantite:
                return jsonify({
                    "error": f"Stock insuffisant pour {ligne.produit.nom}",
                    "produit_id": ligne.produit_id,
                    "stock_disponible": ligne.produit.quantite_stock or 0
                }), 409

        for ligne in commande.lignes:
            ligne.produit.quantite_stock -= ligne.quantite

    # Annulation d'une commande déjà validée : on remet le stock
    if nouveau_statut == "annulee" and ancien_statut == "validee":
        for ligne in commande.lignes:
            ligne.produit.quantite_stock = (ligne.produit.quantite_stock or 0) + ligne.quantite

    commande.statut = nouveau_statut
    db.session.commit()

    return jsonify({
        "message": "Statut modifié",
        "commande": commande_en_dict(commande)
    }), 200