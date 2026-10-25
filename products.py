# products.py
from functools import wraps

from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from database import db
from models import User, Product
from sqlalchemy import text

products_bp = Blueprint(
    "products",
    __name__,
    url_prefix="/api/produits"
)


#####################################################
# CHECK SI ADMIN
#####################################################
def admin_required(function):
    @wraps(function)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = db.session.get(User, int(get_jwt_identity()))

        if user is None:
            return jsonify({"error": "Utilisateur introuvable"}), 401

        if user.role != "admin":
            return jsonify({
                "error": "Accès réservé aux administrateurs"
            }), 403

        return function(*args, **kwargs)

    return wrapper


#####################################################
# LISTE DES PRODUITS
#####################################################

@products_bp.route("/", methods=["GET"])
def get_products():
    products = db.session.execute(
        db.select(Product).order_by(Product.id)
    ).scalars().all()

    return jsonify([
        {
            "id": product.id,
            "nom": product.nom,
            "prix": product.prix
        }
        for product in products
    ]), 200


#####################################################
# DÉTAIL D'UN PRODUIT
#####################################################

@products_bp.route("/<int:product_id>", methods=["GET"])
def get_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "Produit introuvable"}), 404

    return jsonify({
        "id": product.id,
        "nom": product.nom,
        "description": product.description,
        "categorie": product.categorie,
        "prix": product.prix,
        "quantite_stock": product.quantite_stock,
        "date_creation": (
            product.date_creation.isoformat()
            if product.date_creation else None
    )
    }), 200


#####################################################
# ADMIN : CRÉATION D'UN PRODUIT
#####################################################

@products_bp.route("/", methods=["POST"])
@admin_required
def create_product():
    data = request.get_json()

    product = Product(
        nom=data["nom"].strip(),
        description=data.get("description"),
        categorie=data["categorie"].strip(),
        prix=data["prix"],
        quantite_stock=data.get("quantite_stock", 0)
    )

    db.session.add(product)
    db.session.commit()

    return jsonify({
        "message": "Produit créé",
        "id": product.id
    }), 201


#####################################################
# ADMIN : MODIFICATION D'UN PRODUIT
#####################################################

@products_bp.route("/<int:product_id>", methods=["PUT", "PATCH"])
@admin_required
def update_product(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "Produit introuvable"}), 404

    data = request.get_json()

    if "nom" in data:
        product.nom = data["nom"].strip()

    if "description" in data:
        product.description = data["description"]

    if "categorie" in data:
        product.categorie = data["categorie"].strip()

    if "prix" in data:
        product.prix = data["prix"]

    if "quantite_stock" in data:
        product.quantite_stock = data["quantite_stock"]

    db.session.commit()

    return jsonify({
        "message": "Produit modifié",
        "produit": {
            "id": product.id,
            "nom": product.nom,
            "description": product.description,
            "categorie": product.categorie,
            "prix": product.prix,
            "quantite_stock": product.quantite_stock,
            "date_creation": (
                product.date_creation.isoformat()
                if product.date_creation else None
            )
        }
    }), 200


#####################################################
# ADMIN : SUPPRESSION D'UN PRODUIT
#####################################################

@products_bp.route("/<int:product_id>", methods=["DELETE"])
@admin_required
def delete_product(product_id):

    product = db.session.get(Product, product_id)

    if product is None:
        return jsonify({"error": "Produit introuvable"}), 404

    commande = db.session.execute(
        text(
            "SELECT 1 FROM order_item "
            "WHERE produit_id = :product_id LIMIT 1"
        ),
        {"product_id": product_id}
    ).first()

    if commande is not None:
        return jsonify({
            "error": "Ce produit est associé à une commande"
        }), 409

    db.session.delete(product)
    db.session.commit()

    return jsonify({
        "message": "Produit supprimé",
        "id": product_id
    }), 200