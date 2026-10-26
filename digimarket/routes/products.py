from apiflask import APIBlueprint, abort

from sqlalchemy import text

from digimarket.database import db
from digimarket.models import Product
from digimarket.schemas import ProductCreate, ProductUpdate, ProductSummary, ProductOut
from digimarket.auth import admin_required

products_bp = APIBlueprint(
    "products",
    __name__,
    url_prefix="/api/produits",
    tag="Produits"
)



def trouver_produit(product_id):
    product = db.session.get(Product, product_id)

    if product is None:
        abort(404, "Produit introuvable")

    return product


#####################################################
# LISTE DES PRODUITS
#####################################################

@products_bp.get("/")
@products_bp.output(ProductSummary(many=True))
def get_products():
    return db.session.execute(
        db.select(Product).order_by(Product.id)
    ).scalars().all()


#####################################################
# DÉTAIL D'UN PRODUIT
#####################################################

@products_bp.get("/<int:product_id>")
@products_bp.output(ProductOut)
def get_product(product_id):
    return trouver_produit(product_id)


#####################################################
# ADMIN : CRÉATION D'UN PRODUIT
#####################################################

@products_bp.post("/")
@admin_required # Seul un admin a le droit de créer un produit
@products_bp.input(ProductCreate)
@products_bp.output(ProductOut, status_code=201)
@products_bp.doc(security="BearerAuth", responses=[401, 403])
def create_product(json_data):
    product = Product(**json_data)

    db.session.add(product)
    db.session.commit()

    return product


#####################################################
# ADMIN : MODIFICATION D'UN PRODUIT
#####################################################

@products_bp.route("/<int:product_id>", methods=["PUT", "PATCH"])
@admin_required
@products_bp.input(ProductUpdate)
@products_bp.output(ProductOut)
@products_bp.doc(security="BearerAuth", responses=[401, 403, 404])
def update_product(product_id, json_data):
    product = trouver_produit(product_id)

    # Seuls les champs envoyés sont modifiés
    for champ, valeur in json_data.items():
        setattr(product, champ, valeur)

    db.session.commit()

    return product


#####################################################
# ADMIN : SUPPRESSION D'UN PRODUIT
#####################################################

@products_bp.delete("/<int:product_id>")
@admin_required
@products_bp.output({}, status_code=204)
@products_bp.doc(security="BearerAuth", responses=[401, 403, 404, 409])
def delete_product(product_id):
    product = trouver_produit(product_id)

    commande = db.session.execute(
        text(
            "SELECT 1 FROM order_item "
            "WHERE produit_id = :product_id LIMIT 1"
        ),
        {"product_id": product_id}
    ).first()

    if commande is not None:
        abort(409, "Ce produit est associé à une commande")

    db.session.delete(product)
    db.session.commit()