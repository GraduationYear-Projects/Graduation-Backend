from flask import Blueprint
from product.models import Product

product_bp = Blueprint('product', __name__)

@product_bp.route('/products/import', methods=['POST'])
def import_products():
    return Product().import_products()

@product_bp.route('/products', methods=['GET'])
def get_products():
    return Product().get_products()

