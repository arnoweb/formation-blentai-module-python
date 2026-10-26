# schemas.py
from apiflask import Schema
from apiflask.fields import Integer, String, Float, DateTime, Email, List, Nested, Function
from apiflask.validators import Length, Range, OneOf
from marshmallow import pre_load

from models import STATUTS_COMMANDE


#####################################################
# PRODUITS
#####################################################

class ProductUpdate(Schema):
    # Tous les champs sont facultatifs : seuls ceux envoyés sont modifiés
    nom = String(validate=Length(min=1, max=100))
    description = String(allow_none=True)
    categorie = String(validate=Length(min=1, max=50))
    prix = Float(validate=Range(min=0))
    quantite_stock = Integer(validate=Range(min=0))

    @pre_load
    def clean_texts(self, data, **kwargs):
        # Équivalent des .strip() de l'ancienne version
        if isinstance(data, dict):
            for champ in ("nom", "categorie"):
                if isinstance(data.get(champ), str):
                    data[champ] = data[champ].strip()
        return data


class ProductCreate(ProductUpdate):
    # Création : nom, categorie et prix deviennent obligatoires
    nom = String(required=True, validate=Length(min=1, max=100))
    categorie = String(required=True, validate=Length(min=1, max=50))
    prix = Float(required=True, validate=Range(min=0))
    quantite_stock = Integer(load_default=0, validate=Range(min=0))


class ProductSummary(Schema):
    id = Integer()
    nom = String()
    prix = Float()


class ProductOut(ProductSummary):
    description = String(allow_none=True)
    categorie = String()
    quantite_stock = Integer()
    date_creation = DateTime()


#####################################################
# UTILISATEURS
#####################################################

class RegisterIn(Schema):
    email = Email(required=True)
    password = String(required=True, load_only=True, validate=Length(min=8))
    name = String(required=True, validate=Length(min=1, max=100))


class LoginIn(Schema):
    email = String(required=True)
    password = String(required=True, load_only=True)


class UserUpdate(Schema):
    # Tous les champs sont facultatifs : seuls ceux envoyés sont modifiés
    email = Email()
    password = String(load_only=True, validate=Length(min=8))
    name = String(validate=Length(min=1, max=100))


class UserOut(Schema):
    id = Integer()
    email = String()
    nom = String()
    role = String()


class TokenOut(Schema):
    access_token = String()


#####################################################
# COMMANDES
#####################################################

class OrderItemIn(Schema):
    produit_id = Integer(required=True, strict=True)
    quantite = Integer(required=True, strict=True, validate=Range(min=1))


class OrderCreate(Schema):
    adresse_livraison = String(required=True, validate=Length(min=1, max=200))
    lignes = List(Nested(OrderItemIn), required=True, validate=Length(min=1))

    @pre_load
    def clean_address(self, data, **kwargs):
        if isinstance(data, dict) and isinstance(data.get("adresse_livraison"), str):
            data["adresse_livraison"] = data["adresse_livraison"].strip()
        return data


class OrderStatusUpdate(Schema):
    statut = String(required=True, validate=OneOf(STATUTS_COMMANDE))


class OrderItemOut(Schema):
    id = Integer()
    produit_id = Integer()
    produit_nom = String(attribute="produit.nom")
    quantite = Integer()
    prix_unitaire = Float()
    sous_total = Function(lambda ligne: round(ligne.quantite * ligne.prix_unitaire, 2))


class OrderItemListOut(OrderItemOut):
    # Même contenu que OrderItemOut : une classe à part évite que la doc
    # enregistre deux fois le même schéma (liste seule + liste dans OrderDetailOut)
    pass


class OrderOut(Schema):
    id = Integer()
    utilisateur_id = Integer()
    date_commande = DateTime()
    adresse_livraison = String()
    statut = String()
    total = Float()


class OrderDetailOut(OrderOut):
    lignes = Nested(OrderItemOut, many=True)