# Schémas des produits : format du JSON entrant et sortant
from apiflask import PaginationSchema, Schema
from apiflask.fields import DateTime, Float, Integer, List, Nested, String
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
    # nom = String(data_key="name") #On change la clef nom en name en sortie de l'API
    categorie = String()
    prix = Float()


class ProductOut(ProductSummary):
    description = String(allow_none=True)
    quantite_stock = Integer()
    date_creation = DateTime()


# Paramètres de la liste des produits (dans l'URL : ?page=1&per_page=10&categorie=…)
class ProductQuery(Schema):
    page = Integer(load_default=1, validate=Range(min=1))
    per_page = Integer(load_default=10, validate=Range(min=1, max=100))
    categorie = String()
    nom = String()
    prix_min = Float(validate=Range(min=0))
    prix_max = Float(validate=Range(min=0))


# Une page de produits + les informations de pagination
class ProductPage(Schema):
    products = List(Nested(ProductSummary))
    pagination = Nested(PaginationSchema)
