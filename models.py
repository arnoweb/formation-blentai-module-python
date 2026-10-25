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

class Product(db.Model):

    __tablename__ = "product"

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    categorie = db.Column(db.String(50), nullable=False)
    prix = db.Column(db.Float, nullable=False)
    quantite_stock = db.Column(db.Integer, default=0)
    date_creation = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(timezone.utc)
    )

from datetime import datetime
from database import db

#####################################################
# COMMANDE
#####################################################

STATUTS_COMMANDE = ("en_attente", "validee", "expediee", "annulee")
class Order(db.Model):
    # Nom de table explicite : "order" est un mot réservé SQL
    __tablename__ = "order"

    id = db.Column(db.Integer, primary_key=True)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    date_commande = db.Column(db.DateTime, default=datetime.now)
    adresse_livraison = db.Column(db.String(200), nullable=False)
    statut = db.Column(db.String(20), default="en_attente")

    utilisateur = db.relationship("User", backref="commandes")

    # Supprimer une commande supprime ses lignes
    lignes = db.relationship(
        "OrderItem",
        back_populates="commande",
        cascade="all, delete-orphan"
    )

    @property
    def total(self):
        return round(sum(ligne.quantite * ligne.prix_unitaire for ligne in self.lignes), 2)


#####################################################
# LIGNE DE COMMANDE
#####################################################

class OrderItem(db.Model):
    __tablename__ = "order_item"

    id = db.Column(db.Integer, primary_key=True)
    commande_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    produit_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    # Prix au moment de la commande : il ne bouge pas si le prix du produit change ensuite
    prix_unitaire = db.Column(db.Float, nullable=False)

    commande = db.relationship("Order", back_populates="lignes")
    produit = db.relationship("Product")