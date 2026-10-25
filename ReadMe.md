##DEMO APP - BLENT.IA - CASE DIGIMARKET - ECOMMERCE WEBSITE


# On test la création d'un utilisateur dont le role est client ou admin
# Cela créé une entrée dans la base
# Le -s pour voir les logs (print)
python -m pytest test_users.py -v -s --role=admin
python -m pytest test_users.py -v -s --role=client




