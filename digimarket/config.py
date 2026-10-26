# Configuration de l'application, lue depuis .env.local
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

# .env.local est à la racine du projet, un niveau au-dessus du package
load_dotenv(Path(__file__).resolve().parent.parent / ".env.local")


class Config:
    # SQLite : le fichier est créé dans instance/
    SQLALCHEMY_DATABASE_URI = "sqlite:///digimarket.db"

    # JWT : clé secrète lue dans .env.local, token valable 15 minutes
    JWT_SECRET_KEY = os.environ["JWT_SECRET_KEY"]
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=15)

    # Les erreurs de validation des schémas renvoient 400
    VALIDATION_ERROR_STATUS_CODE = 400

    # Documentation Swagger : texte affiché sous le titre (Markdown accepté)
    DESCRIPTION = """
API e-commerce **DigiMarket** : catalogue de produits, comptes utilisateurs et commandes.

## Authentification
1. Connectez-vous avec `POST /api/auth/login` pour obtenir un `access_token`.
2. Cliquez sur **Authorize** et collez le token, sans `Bearer` devant.
3. Le token est valable **15 minutes**.

## Rôles
- **client** : consulte les produits, passe et suit ses commandes.
- **admin** : gère les produits, les utilisateurs et le statut des commandes.

## Codes de réponse
| Code | Signification |
|---|---|
| 400 | données invalides |
| 401 | non connecté ou token expiré |
| 403 | connecté, mais pas les droits |
| 404 | ressource introuvable |
| 409 | conflit (stock insuffisant, transition de statut interdite…) |
"""