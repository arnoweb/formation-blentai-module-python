# Package de l'API DigiMarket : create_app() construit l'application
from apiflask import APIFlask
from flask_jwt_extended import JWTManager
from sqlalchemy import text

from digimarket.cli import create_admin
from digimarket.config import Config
from digimarket.database import db
from digimarket.routes.orders import orders_bp
from digimarket.routes.products import products_bp
from digimarket.routes.users import users_bp


def create_app(config=None):
    app = APIFlask(__name__, title="DigiMarket API", version="1.0.0")
    app.config.from_object(Config)

    # Les tests peuvent surcharger la configuration (TESTING, base de test…)
    if config:
        app.config.update(config)

    app.security_schemes = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }

    JWTManager(app)
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

    # Commande create-admin : voir digimarket/cli.py
    app.cli.add_command(create_admin)

    @app.route("/")
    def index():
        return "BlentAI - API for E-commerce"

    return app