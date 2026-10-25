# users.py
from flask import Blueprint, jsonify, request
from models import User
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from database import db


users_bp = Blueprint("users", __name__, url_prefix="/api/auth")

@users_bp.route("/", methods=["GET"])
def get_users():
    return jsonify({"message": "Liste des utilisateurs"})

# Création d'un utilisateur
@users_bp.route("/register", methods=["POST"])
def create_user():
    data = request.get_json()
    user = User(
        email=data["email"],
        nom=data["name"],
        password_hash=generate_password_hash(data["password"]),
        role=data["role"]
    )
    #On prépare l'ajout
    db.session.add(user)
    #On enregistre les modifications dans la base de données
    db.session.commit()
    #On retourne la réponse
    return jsonify({"message": "Utilisateur créé"}), 201

# Modification d'un utilisateur
@users_bp.route("/register/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    data = request.get_json()
    user = db.session.get(User, user_id)

    if user is None:
        return jsonify({"error": "Utilisateur introuvable"}), 404

    if "email" in data:
        user.email = data["email"]

    if "name" in data:
        user.nom = data["name"]

    if "password" in data:
        user.password_hash = generate_password_hash(data["password"])

    #On enregistre les modifications dans la base de données
    db.session.commit()
    return jsonify({
        "message": "Utilisateur modifié",
        "id": user.id,
        "email": user.email
    }), 200

@users_bp.route("/login", methods=["POST"])
def login():

    data = request.get_json()

    if not isinstance(data, dict):
        return jsonify({"error": "Un objet JSON est attendu"}), 400

    email = data.get("email")
    password = data.get("password")

    # On check email et password sont pas vides
    if (
        not isinstance(email, str)
        or not isinstance(password, str)
        or not email
        or not password
    ):
        return jsonify({"error": "Email et mot de passe requis"}), 400

    # On cherche le compte dans la BDD
    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    # On vérifie le mdp sinon 401
    if user is None or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Identifiants incorrects"}), 401

    # On créé le token qui contient l'ID du user
    # C'est cet ID que l'on va lire ensuite et on pourra récupérer les rôles, donc fonctionnalités par rôle
    access_token = create_access_token(identity=str(user.id))

    return jsonify({"access_token": access_token}), 200



@users_bp.route("/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    return jsonify({"message": "Utilisateur supprimé", "id": user_id})