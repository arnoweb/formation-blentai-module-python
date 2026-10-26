# API - Application principale
from flask import Flask
from users import users_bp
from products import products_bp
from orders import orders_bp

from sqlalchemy import text
from database import db
from dotenv import load_dotenv
from pathlib import Path

import os
from datetime import timedelta
from flask_jwt_extended import JWTManager

import click
from werkzeug.security import generate_password_hash
from models import User
from apiflask import APIFlask 

# On charge le fichier .env.local
load_dotenv(Path(__file__).resolve().parent / ".env.local")

app = APIFlask(__name__, title="DigiMarket API", version="1.0.0")

app.config["VALIDATION_ERROR_STATUS_CODE"] = 400
app.security_schemes = {
    "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
}

# On utilise Flask JWT - on lit le fichier .env - durée du token Secret de 15 minutes
app.config["JWT_SECRET_KEY"] = os.environ["JWT_SECRET_KEY"]
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=15)

jwt = JWTManager(app)

# SQLITE
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///digimarket.db"
db.init_app(app)

# On vérifie la connexion à la base de données avant de démarrer l'application.
with app.app_context():
    try:
        db.session.execute(text("SELECT 1"))
        db.session.remove()
        app.logger.info("Connexion à SQLite réussie")

    except Exception:
        app.logger.exception("Impossible de se connecter à SQLite")
        raise  # Arrête le démarrage si la connexion échoue.


app.register_blueprint(users_bp)
app.register_blueprint(products_bp)
app.register_blueprint(orders_bp)


#####################################################
# COMMANDE : CRÉATION D'UN ADMIN
#####################################################
# L'API n'autorise plus le choix du rôle, donc on crée les admins en ligne de commande
# flask --app app create-admin admin@test.fr motdepasse
@app.cli.command("create-admin")
@click.argument("email")
@click.argument("password")
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


@app.route("/")
def index():
    return "BlentAI - API for E-commerce"

if __name__ == "__main__":
    app.run(debug=True, port=5001)