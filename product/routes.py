from flask import Blueprint
from product.models import Product

product_bp = Blueprint('product', __name__)

@product_bp.route('/api/products/import/', methods=['POST'])
def import_products():
    return Product().insert_products_from_json()

@product_bp.route('/api/products/', methods=['GET'])
def get_products():
    return Product().get_products()

@product_bp.route("/api/products/<product_id>/", methods=["GET"])
def get_product_id(product_id):
    return Product().get_product_id(product_id)

@product_bp.route("/api/search/", methods=["GET"])
def search_products():
    return Product().search_products()

