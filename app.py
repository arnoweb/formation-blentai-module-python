from flask import Flask
from users import users_bp
from admin import admin_bp
from sqlalchemy import text
from database import db

app = Flask(__name__)

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


app.register_blueprint(users_bp, url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/admin")

@app.route("/")
def index():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True, port=5001)