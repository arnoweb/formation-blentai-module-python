from functools import wraps

from apiflask import abort
from flask_jwt_extended import get_jwt_identity, jwt_required

from digimarket.database import db
from digimarket.models import User


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
