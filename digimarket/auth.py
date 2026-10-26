from digimarket.database import db
from digimarket.models import User
from apiflask import abort
from functools import wraps
from flask_jwt_extended import jwt_required, get_jwt_identity

#####################################################
# CHECK SI ADMIN
#####################################################
def admin_required(function):
    @wraps(function)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = db.session.get(User, int(get_jwt_identity()))

        if user is None:
            abort(401, "Utilisateur introuvable")

        if user.role != "admin":
            abort(403, "Accès réservé aux administrateurs")

        return function(*args, **kwargs)

    return wrapper