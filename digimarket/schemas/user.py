# Schémas des utilisateurs : format du JSON entrant et sortant
from apiflask import Schema
from apiflask.fields import Email, Integer, String
from apiflask.validators import Length
from marshmallow import EXCLUDE


class RegisterIn(Schema):
    # Il faut connaitre le role, ce qui est inconnu on l'exclut
    class Meta:
        unknown = EXCLUDE

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


class MessageOut(Schema):
    message = String()
