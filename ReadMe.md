##DEMO APP - BLENT.IA - CASE DIGIMARKET - ECOMMERCE WEBSITE

# Lancer les tests de l'API
pytest -v

# Lancer les tests de l'API - endpoint 

# On test la création d'un utilisateur dont le role est client ou admin
# Cela créé une entrée dans la base
# Le -s pour voir les logs (print)
python -m pytest test_users.py -v -s --role=admin
python -m pytest test_users.py -v -s --role=client

# Créer un compte admin
flask --app app create-admin admin@test.fr motdepasse

# On test la création d'un produit
# Cela créé une entrée dans la base
# Le -s pour voir les logs (print)
python -m pytest test_products.py -v -s
# Liste produits
python -m pytest test_products.py::test_liste_produits -v -s
# Création produit
python -m pytest test_products.py::test_creation_produit -v -s
# Modification produit
python -m pytest test_products.py::test_modification_produit -v -s
# Suppression produit
python -m pytest test_products.py::test_suppression_produit -v -s
# Creation produit - par un client et pas un admin
python -m pytest test_products.py::test_creation_produit_client_refusee -v -s


# 1. Créer un compte admin
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.fr","password":"motdepasse","name":"Admin","role":"admin"}'

# 2. Se connecter et récupérer le token
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@test.fr","password":"motdepasse"}'

# 3. Créer un produit (remplacez VOTRE_TOKEN par l'access_token reçu)
curl -X POST http://localhost:5001/api/produits/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer VOTRE_TOKEN" \
  -d '{"nom":"Clavier","description":"Clavier sans fil","categorie":"Informatique","prix":49.90,"quantite_stock":10}'

# 4. Lister
curl http://localhost:5001/api/produits/


1. Créer un compte en essayant de devenir admin
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"client@test.fr","password":"motdepasse","name":"Client","role":"admin"}'
Attendu : {"message": "Utilisateur créé"}. Le compte est créé, mais le "role": "admin" doit être ignoré. Si l’email existe déjà, prenez-en un autre.

2. Se connecter et garder le token dans une variable
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"client@test.fr","password":"motdepasse"}' \
  | python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo $TOKEN
Si echo n’affiche rien, la connexion a échoué. Relancez la commande sans la partie | python3 ... pour voir l’erreur.

3. Vérifier le rôle
curl http://localhost:5001/api/auth/me -H "Authorization: Bearer $TOKEN"
Attendu : "role": "client". Si vous voyez "admin", la correction de users.py n’est pas en place.

4. Essayer de créer un produit en tant que client
curl -i -X POST http://localhost:5001/api/produits/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"nom":"Produit pirate","categorie":"Test","prix":1}'