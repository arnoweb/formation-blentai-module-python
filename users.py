# users.py
from flask import Blueprint, jsonify

users_bp = Blueprint("users", __name__)

@users_bp.route("/", methods=["GET"])
def get_users():
    return jsonify({"message": "Liste des utilisateurs"})

@users_bp.route("/", methods=["POST"])
def create_user():
    return jsonify({"message": "Utilisateur créé"}), 201

@users_bp.route("/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    return jsonify({"message": "Utilisateur modifié", "id": user_id})

@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    return jsonify({"message": "Utilisateur supprimé", "id": user_id})