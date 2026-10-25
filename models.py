from database import db
from datetime import datetime, timezone

class User(db.Model):
    # Nom de la table déjà présente dans SQLite.
    __tablename__ = "user"

    # Identifiant unique de chaque utilisateur.
    id = db.Column(db.Integer, primary_key=True)

    # Adresse obligatoire et unique.
    email = db.Column(db.String(120), unique=True, nullable=False)

    # Mot de passe obligatoire et unique.
    password_hash = db.Column(db.String(120), unique=True, nullable=False)

    # Nom obligatoire.
    nom = db.Column(db.String(100), nullable=False)

    # Role Client ou Admin et on met client par défaut
    role = db.Column(db.String(20), nullable=False, default="client")

    # Date de création de l'utilisateur
    date_creation = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
)
