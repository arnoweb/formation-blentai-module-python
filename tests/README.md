# Tests de l'API DigiMarket

Tests automatisés de l'API avec **pytest**. Ils appellent les routes via le client de test Flask, sans lancer de serveur, puis vérifient les réponses HTTP et l'état de la base.

## Prérequis

Variables à définir dans `.env.local`, à la racine du projet :

| Variable | Rôle |
|---|---|
| `TEST_EMAIL_DOMAIN` | domaine des emails des comptes de test (ex. `example.com`) |
| `TEST_CLIENT_PASSWORD` | mot de passe des comptes client créés par les tests |
| `TEST_ADMIN_PASSWORD` | mot de passe des comptes admin créés par les tests |

Le fichier `pytest.ini`, à la racine, configure pytest :

```ini
[pytest]
testpaths = tests   # pytest cherche les tests dans ce dossier
pythonpath = .      # permet d'importer app, models… depuis la racine
```

## Lancer les tests

Toutes les commandes se lancent **depuis la racine du projet**, avec l'environnement virtuel activé.

| Objectif | Commande |
|---|---|
| tous les tests | `pytest -v` |
| un fichier | `pytest tests/test_orders.py -v` |
| un seul test | `pytest tests/test_orders.py::test_order_detail -v` |
| afficher les `print` (appels API) | ajouter `-s` |
| s'arrêter à la première erreur | ajouter `-x` |
| relancer seulement les tests en échec | ajouter `--lf` |

## Organisation

```
tests/
├── conftest.py        fixtures partagées par tous les fichiers
├── test_routes.py     routes publiques et protection globale
├── test_users.py      inscription, connexion, modification, profil
├── test_products.py   CRUD produits et droits d'accès
└── test_orders.py     commandes, stock et statuts
```

## Fixtures

Une fixture prépare ce dont un test a besoin (un client HTTP, un compte connecté, un produit…). Le test la reçoit simplement en paramètre. Les fixtures de `conftest.py` sont disponibles dans tous les fichiers, sans import.

| Fixture | Fichier | Fournit |
|---|---|---|
| `client` | conftest.py | le client de test Flask, pour appeler l'API |
| `auth_headers` | conftest.py | une fonction `auth_headers("client")` ou `auth_headers("admin")` qui crée un compte, le connecte et renvoie le header `Authorization`. Le compte admin est passé en rôle admin directement en base, car l'API crée toujours des clients. |
| `product` | conftest.py | un produit créé par un admin : `{"id", "headers"}` (headers admin). Supprimé à la fin du test. |
| `user` | test_users.py | un utilisateur inscrit : `{"id", "email", "password", "name"}` |
| `user_headers` | test_users.py | le header `Authorization` de cet utilisateur |
| `order` | test_orders.py | une commande de 2 unités du produit, passée par un client : `{"id", "headers", "admin_headers", "product_id", "quantite"}`. Supprimée à la fin du test. |

Dépendances entre fixtures :

```
order → product → auth_headers → client
user_headers → user → client
```

## Contenu des tests

### test_routes.py

| Test | Vérifie |
|---|---|
| `test_routes_get` | `/`, `/api/auth/` et `/api/produits/` répondent 200 |
| `test_routes_get_unauthorized` | `/api/commandes` sans token renvoie 401 |

### test_users.py

| Test | Vérifie |
|---|---|
| `test_user_register` | l'inscription renvoie 201 et crée le compte en base, toujours avec le rôle `client`, même si `"role": "admin"` est envoyé |
| `test_user_login` | la connexion renvoie 200 et un token non vide |
| `test_user_update_own_account` | un utilisateur connecté peut modifier son email et son nom (200, base à jour) |
| `test_user_me_without_token_401` | `/api/auth/me` sans token renvoie 401 |
| `test_user_me_with_token` | `/api/auth/me` avec token renvoie l'id, l'email et le rôle de l'utilisateur |

### test_products.py

| Test | Vérifie |
|---|---|
| `test_products_list` | la liste renvoie 200 et contient le produit créé |
| `test_product_detail` | le détail renvoie les bonnes valeurs (nom, prix, stock…) |
| `test_product_create` | le produit créé existe en base avec les bonnes valeurs |
| `test_product_modify` | un admin peut modifier un produit (200, réponse et base à jour) |
| `test_product_delete` | un admin peut supprimer un produit (204), qui devient introuvable (404) |
| `test_product_protection` | POST, PUT, DELETE **sans token** → 401 |
| `test_create_delete_for_nonadmin` | POST, PUT, DELETE avec un token **client** → 403 |

### test_orders.py

| Test | Vérifie |
|---|---|
| `test_order_detail` | le client retrouve sa commande : statut `en_attente`, lignes et total corrects |
| `test_order_list_without_token_401` | la liste des commandes sans token renvoie 401 |
| `test_order_insufficient_stock_409` | commander plus que le stock disponible renvoie 409 |
| `test_order_validate_then_cancel_restores_stock` | la validation décrémente le stock, l'annulation le remet |
| `test_order_invalid_transition_409` | une commande annulée ne peut plus changer de statut (409) |
| `test_order_status_as_client_403` | un client ne peut pas changer le statut d'une commande (403) |

## Codes HTTP vérifiés

| Code | Signification dans l'API |
|---|---|
| 200 | succès |
| 201 | ressource créée |
| 204 | suppression réussie, sans contenu |
| 401 | pas de token (ou token invalide) : il faut se connecter |
| 403 | connecté, mais pas le droit (ex. un client sur une route admin) |
| 404 | ressource introuvable |
| 409 | conflit : stock insuffisant, transition de statut interdite |

## À savoir

- **Les tests utilisent la vraie base SQLite** (`instance/digimarket.db`). Les produits et les commandes de test sont supprimés à la fin de chaque test, mais **les comptes utilisateurs créés restent en base**.
- Chaque compte de test a un email unique (`uuid4`), donc les tests peuvent être relancés sans conflit.
- Une erreur dans une fixture apparaît comme **ERROR** (la préparation a échoué). Une assertion fausse dans un test apparaît comme **FAILED**.