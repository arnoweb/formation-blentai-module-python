# Routes des utilisateurs : inscription, connexion, profil, modification
from apiflask import APIBlueprint, abort
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
from werkzeug.security import check_password_hash, generate_password_hash

from digimarket.auth import admin_required
from digimarket.database import db
from digimarket.models import Order, User
from digimarket.schemas import (
    LoginIn,
    MessageOut,
    RegisterIn,
    TokenOut,
    UserOut,
    UserUpdate,
)

users_bp = APIBlueprint("users", __name__, url_prefix="/api/auth", tag="Utilisateurs")


# Liste des utilisateurs : réservée aux admins
@users_bp.route("/", methods=["GET"])
@admin_required
@users_bp.output(UserOut(many=True))
@users_bp.doc(
    summary="Lister les utilisateurs", security="BearerAuth", responses=[401, 403]
)
def get_users():
    return db.session.execute(db.select(User).order_by(User.id)).scalars().all()


# Création d'un utilisateur (toujours avec le rôle client)
@users_bp.route("/register", methods=["POST"])
@users_bp.input(RegisterIn)
@users_bp.output(MessageOut, status_code=201)
@users_bp.doc(summary="Créer un compte client")
def create_user(json_data):
    user = User(
        email=json_data["email"],
        nom=json_data["name"],
        password_hash=generate_password_hash(json_data["password"]),
        role="client",
    )
    db.session.add(user)
    db.session.commit()

    return {"message": "Utilisateur créé"}


# Connexion : renvoie un token JWT
@users_bp.route("/login", methods=["POST"])
@users_bp.input(LoginIn, example={"email": "admin@example.com", "password": "XXXXXXX"})
@users_bp.output(TokenOut)
@users_bp.doc(summary="Se connecter et obtenir un token", responses=[401])
def login(json_data):
    user = db.session.execute(
        db.select(User).filter_by(email=json_data["email"])
    ).scalar_one_or_none()

    # On vérifie le mdp sinon 401
    if user is None or not check_password_hash(
        user.password_hash, json_data["password"]
    ):
        abort(401, "Identifiants incorrects")

    # Le token contient l'ID du user : on le relira ensuite pour retrouver son rôle
    return {"access_token": create_access_token(identity=str(user.id))}


# Profil de l'utilisateur connecté
@users_bp.route("/me", methods=["GET"])
@jwt_required()
@users_bp.output(UserOut)
@users_bp.doc(summary="Mon profil", security="BearerAuth", responses=[401])
def get_current_user():
    user = db.session.get(User, int(get_jwt_identity()))

    if user is None:
        abort(401, "Utilisateur introuvable")

    return user


# Modification de son propre compte
@users_bp.route("/register/<int:user_id>", methods=["PUT"])
@jwt_required()
@users_bp.input(UserUpdate)
@users_bp.output(UserOut)
@users_bp.doc(
    summary="Modifier mon compte", security="BearerAuth", responses=[401, 403, 404]
)
def update_user(user_id, json_data):
    # On ne peut modifier que son propre compte
    if int(get_jwt_identity()) != user_id:
        abort(403, "Accès refusé")

    user = db.session.get(User, user_id)

    if user is None:
        abort(404, "Utilisateur introuvable")

    if "email" in json_data:
        user.email = json_data["email"]

    if "name" in json_data:
        user.nom = json_data["name"]

    if "password" in json_data:
        user.password_hash = generate_password_hash(json_data["password"])

    db.session.commit()

    return user


# Suppression d'un utilisateur : réservée aux admins
@users_bp.route("/<int:user_id>", methods=["DELETE"])
@admin_required
@users_bp.output({}, status_code=204)
@users_bp.doc(
    summary="Supprimer un utilisateur",
    security="BearerAuth",
    responses=[401, 403, 404, 409],
)
def delete_user(user_id):
    # Un admin ne peut pas supprimer son propre compte
    if int(get_jwt_identity()) == user_id:
        abort(409, "Un administrateur ne peut pas supprimer son propre compte")

    user = db.session.get(User, user_id)

    if user is None:
        abort(404, "Utilisateur introuvable")

    # On garde l'historique : un utilisateur qui a des commandes ne peut pas être supprimé
    a_des_commandes = db.session.execute(
        db.select(Order.id).filter_by(utilisateur_id=user_id).limit(1)
    ).first()

    if a_des_commandes is not None:
        abort(409, "Cet utilisateur a des commandes")

    db.session.delete(user)
    db.session.commit()
