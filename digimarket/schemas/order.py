# Schémas des commandes : format du JSON entrant et sortant
from apiflask import Schema
from apiflask.fields import Integer, String, Float, DateTime, List, Nested, Function
from apiflask.validators import Length, Range, OneOf
from marshmallow import pre_load

from digimarket.models import STATUTS_COMMANDE


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