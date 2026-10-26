![Python](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)![Flask](https://img.shields.io/badge/Flask-3.1-000000?logo=flask&logoColor=white)![APIFlask](https://img.shields.io/badge/APIFlask-3.1-2F9E44)![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.1-D71F00?logo=sqlalchemy&logoColor=white)![SQLite](https://img.shields.io/badge/SQLite-3-003B57?logo=sqlite&logoColor=white)![JWT](https://img.shields.io/badge/Auth-JWT-000000?logo=jsonwebtokens&logoColor=white)![OpenAPI](https://img.shields.io/badge/OpenAPI-3.1-6BA539?logo=openapiinitiative&logoColor=white)![pytest](https://img.shields.io/badge/tests-pytest-0A9EDC?logo=pytest&logoColor=white)

# API REST E-commerce avec Flask
### **Formation Blent.ai - nov 2026 · Examen du module Python**
Auteur : **Arnaud Breton**

[![Logo Blent.ai](docs/images/blentai-logo.png)](https://www.blent.ai)



API REST e-commerce développée en **Python avec Flask**, dans le cadre de l'**examen du module Python de la formation BlentAI** (cas pratique *DigiMarket*).

Elle gère un catalogue de produits, des comptes utilisateurs (clients et administrateurs) et des commandes, avec authentification par token JWT et documentation Swagger générée automatiquement.

---

## Sommaire

- [Lancer l'application](#lancer-lapplication)
- [Documentation Swagger](#documentation-swagger)
- [L'API en bref](#lapi-en-bref)
- [Base de données](#base-de-données)
- [Exemples d'appels avec curl](#exemples-dappels-avec-curl)
- [Tests](#tests)

---

## Lancer l'application

### 1. Prérequis

- Python 3.13
- un environnement virtuel dans `.venv`

```bash
python -m venv .venv
source .venv/bin/activate
pip install apiflask flask-sqlalchemy flask-jwt-extended python-dotenv pytest
```

### 2. Configuration

Créer un fichier `.env.local` à la racine (il n'est pas versionné) :

```ini
JWT_SECRET_KEY=une-cle-longue-et-aleatoire

# Utilisées uniquement par les tests
TEST_EMAIL_DOMAIN=example.com
TEST_CLIENT_PASSWORD=MotDePasseClient2026!
TEST_ADMIN_PASSWORD=MotDePasseAdmin2026!
```

`JWT_SECRET_KEY` sert à signer les tokens. Elle reste sur le serveur et ne doit jamais être partagée.

### 3. Créer un administrateur

L'inscription par l'API crée toujours un compte **client**. Les administrateurs se créent en ligne de commande :

```bash
flask --app digimarket create-admin admin@example.com MotDePasse2026!
```

Pour réinitialiser le mot de passe d'un compte :

```bash
flask --app digimarket set-password admin@example.com NouveauMotDePasse2026!
```

### 4. Démarrer l'API

```bash
flask --app digimarket run --debug --port 5001
```

L'API est disponible sur `http://localhost:5001`. Avec `--debug`, le serveur redémarre automatiquement à chaque modification du code.

---

## Documentation Swagger

| URL | Contenu |
|---|---|
| [http://localhost:5001/docs](http://localhost:5001/docs) | Swagger UI : documentation interactive, avec « Try it out » |
| [http://localhost:5001/openapi.json](http://localhost:5001/openapi.json) | spécification OpenAPI, importable dans Postman, Insomnia, Bruno… |

Pour tester les routes protégées dans Swagger :

1. `POST /api/auth/login` → **Try it out** → **Execute**, puis copier l'`access_token` ;
2. bouton **Authorize** en haut de la page → coller le token, **sans** `Bearer` devant ;
3. les routes avec un cadenas sont maintenant accessibles (le token expire au bout de 15 minutes).

---

## L'API en bref

| Ressource | Préfixe | Accès |
|---|---|---|
| Santé | `/health` | public |
| Utilisateurs | `/api/auth` | inscription et connexion publiques, le reste avec token |
| Produits | `/api/produits` | lecture publique, écriture réservée aux admins |
| Commandes | `/api/commandes` | avec token : un client voit ses commandes, un admin les voit toutes et change leur statut |

Règles métier principales :

- la liste des produits est **paginée** et **filtrable** (catégorie, nom, prix) ;
- le stock est vérifié à la création d'une commande, **décrémenté à la validation** et **remis** en cas d'annulation ;
- statuts d'une commande : `en_attente` → `validee` → `expediee`, avec `annulee` possible avant l'expédition ;
- un produit présent dans une commande, ou un utilisateur qui a des commandes, ne peut pas être supprimé (409).

### Vérifier que l'API fonctionne : `/health`

```bash
curl -i http://localhost:5001/health
```

| Réponse | Signification |
|---|---|
| `200` `{"status": "ok", "database": "ok"}` | l'API répond et accède à sa base |
| `503` `{"status": "error", "database": "error"}` | l'API répond, mais la base est inaccessible |

### Organisation du code

```
digimarket/
├── __init__.py     create_app() : assemble l'application
├── config.py       configuration (base, JWT, documentation)
├── database.py     instance SQLAlchemy
├── auth.py         décorateur admin_required
├── cli.py          commandes create-admin et set-password
├── models/         tables de la base (User, Product, Order, OrderItem)
├── schemas/        format des JSON en entrée et en sortie (validation + documentation)
└── routes/         endpoints (health, users, products, orders)
```

---

## Base de données

L'API utilise **SQLite** : la base est un simple fichier, `instance/digimarket.db`, sans serveur à installer.

L'accès passe par l'ORM **SQLAlchemy**, donc le code ne dépend pas de SQLite. Pour utiliser une autre base (PostgreSQL, MySQL…), il suffit de changer `SQLALCHEMY_DATABASE_URI` dans `digimarket/config.py` et d'installer le pilote correspondant, par exemple :

```python
SQLALCHEMY_DATABASE_URI = "postgresql://utilisateur:motdepasse@localhost:5432/digimarket"
```

### Exemples de requêtes SQL

À lancer depuis la racine du projet. L'option `-header -column` affiche un tableau lisible.

Lister les utilisateurs (le mot de passe n'est stocké que sous forme de hash) :

```bash
sqlite3 -header -column instance/digimarket.db "SELECT id, email, nom, role FROM user ORDER BY id;"
```

Lister les administrateurs :

```bash
sqlite3 -header -column instance/digimarket.db "SELECT id, email FROM user WHERE role = 'admin';"
```

Produits en stock faible (moins de 10 unités) :

```bash
sqlite3 -header -column instance/digimarket.db "SELECT id, nom, categorie, prix, quantite_stock FROM product WHERE quantite_stock < 10 ORDER BY quantite_stock;"
```

Nombre de produits et prix moyen par catégorie :

```bash
sqlite3 -header -column instance/digimarket.db "SELECT categorie, COUNT(*) AS nb, ROUND(AVG(prix), 2) AS prix_moyen FROM product GROUP BY categorie;"
```

Commandes avec leur client et leur total :

```bash
sqlite3 -header -column instance/digimarket.db "SELECT o.id, u.email, o.statut, ROUND(SUM(l.quantite * l.prix_unitaire), 2) AS total FROM \"order\" o JOIN user u ON u.id = o.utilisateur_id JOIN order_item l ON l.commande_id = o.id GROUP BY o.id ORDER BY o.id;"
```

Détail des lignes d'une commande (ici la commande n°1) :

```bash
sqlite3 -header -column instance/digimarket.db "SELECT p.nom, l.quantite, l.prix_unitaire FROM order_item l JOIN product p ON p.id = l.produit_id WHERE l.commande_id = 1;"
```

`order` est un mot réservé en SQL, d'où les guillemets autour du nom de la table.

---

## Exemples d'appels avec curl

L'API doit tourner sur le port 5001.

### Authentification

Créer un compte client :

```bash
curl -X POST http://localhost:5001/api/auth/register -H "Content-Type: application/json" -d '{"email":"client@example.com","password":"MotDePasse2026!","name":"Client Test"}'
```

Se connecter et garder le token dans une variable :

```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login -H "Content-Type: application/json" -d '{"email":"admin@example.com","password":"MotDePasse2026!"}' | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")
```

Voir son profil :

```bash
curl http://localhost:5001/api/auth/me -H "Authorization: Bearer $TOKEN"
```

### Produits

Lister les produits (paginé) :

```bash
curl "http://localhost:5001/api/produits/?page=1&per_page=10"
```

Filtrer par catégorie, nom et prix :

```bash
curl "http://localhost:5001/api/produits/?categorie=Informatique&nom=clavier&prix_max=100"
```

Créer un produit (admin) :

```bash
curl -X POST http://localhost:5001/api/produits/ -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"nom":"Clavier mécanique","description":"Clavier sans fil","categorie":"Informatique","prix":89.90,"quantite_stock":25}'
```

Modifier un produit (admin) :

```bash
curl -X PATCH http://localhost:5001/api/produits/1 -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"prix":79.90}'
```

### Commandes

Passer une commande :

```bash
curl -X POST http://localhost:5001/api/commandes -H "Content-Type: application/json" -H "Authorization: Bearer $TOKEN" -d '{"adresse_livraison":"12 rue des Tests, 75000 Paris","lignes":[{"produit_id":1,"quantite":2}]}'
```

Lister ses commandes :

```bash
curl http://localhost:5001/api/commandes -H "Authorization: Bearer $TOKEN"
```

Valider une commande (admin) :

```bash
curl -X PATCH "http://localhost:5001/api/commandes/1?statut=validee" -H "Authorization: Bearer $TOKEN"
```

### Utilisateurs (admin)

Lister les utilisateurs :

```bash
curl http://localhost:5001/api/auth/ -H "Authorization: Bearer $TOKEN"
```

Supprimer un utilisateur :

```bash
curl -i -X DELETE http://localhost:5001/api/auth/5 -H "Authorization: Bearer $TOKEN"
```

---

## Tests

Les tests sont écrits avec **pytest** et se trouvent dans le dossier [`tests/`](tests/). Ils utilisent **leur propre base SQLite**, créée dans un dossier temporaire à chaque lancement : la base `instance/digimarket.db` n'est jamais modifiée.

### Lancer les tests

```bash
pytest -v
```

| Objectif | Commande |
|---|---|
| un fichier | `pytest tests/test_orders.py -v` |
| un seul test | `pytest tests/test_orders.py::test_order_detail -v` |
| afficher les `print` | ajouter `-s` |

Le détail de chaque test et des fixtures est dans [tests/README.md](tests/README.md).

### Hook pre-commit

Un hook git lance les tests **avant chaque commit**. S'ils échouent, le commit est annulé.

Le dossier `.git/hooks/` n'est pas versionné : après un clonage, il faut recréer le hook. Créer le fichier `.git/hooks/pre-commit` :

```sh
#!/bin/sh

# Se place à la racine du projet.
cd "$(git rev-parse --show-toplevel)" || exit 1

# Lance les tests des routes avant chaque commit.
.venv/bin/python -m pytest tests/test_routes.py -v
```

puis le rendre exécutable :

```bash
chmod +x .git/hooks/pre-commit
```

Pour vérifier **tous** les tests avant chaque commit, remplacer la dernière ligne par `.venv/bin/python -m pytest -v`.