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