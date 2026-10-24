# admin.py - API pour les administrateurs
from flask import Blueprint, jsonify

admin_bp = Blueprint("admin", __name__)

@admin_bp.route("/", methods=["GET"])
def get_admin():
    return jsonify({"message": "Liste des administrateurs"})

@admin_bp.route("/", methods=["POST"])
def create_admin():
    return jsonify({"message": "Administrateur créé"}), 201

@admin_bp.route("/<int:admin_id>", methods=["PUT"])
def update_admin(admin_id):
    return jsonify({"message": "Administrateur modifié", "id": admin_id})