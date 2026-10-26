from datetime import UTC, datetime

from digimarket.database import db


class User(db.Model):

    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="client")
    date_creation = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC)
)