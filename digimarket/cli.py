# Commandes en ligne de commande : flask --app app create-admin email motdepasse
import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from digimarket.database import db
from digimarket.models import User


# L'API n'autorise plus le choix du rôle, donc on crée les admins en ligne de commande
@click.command("create-admin")
@click.argument("email")
@click.argument("password")
@with_appcontext
def create_admin(email, password):
    existant = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    if existant is not None:
        print(f"Un utilisateur existe déjà avec l'email {email}")
        return

    user = User(
        email=email,
        nom="Admin",
        password_hash=generate_password_hash(password),
        role="admin"
    )
    db.session.add(user)
    db.session.commit()
    print(f"Admin créé : {email}")