# Schémas des produits : format du JSON entrant et sortant
from apiflask import Schema
from apiflask.fields import Integer, String, Float, DateTime
from apiflask.validators import Length, Range
from marshmallow import pre_load


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
    #nom = String(data_key="name") #On change la clef nom en name en sortie de l'API
    prix = Float()


class ProductOut(ProductSummary):
    description = String(allow_none=True)
    categorie = String()
    quantite_stock = Integer()
    date_creation = DateTime()