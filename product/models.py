from flask import Flask, jsonify, request, session, redirect
from app import db
import uuid
import json
import os

class Product:
    
    def insert_products_from_json(self, json_folder_path='data'):
        # Insert products from JSON files in the specified folder into MongoDB
        try:
            # Get all JSON files from the folder
            json_files = [f for f in os.listdir(json_folder_path) if f.endswith('.json')]
            
            for json_file in json_files:
                file_path = os.path.join(json_folder_path, json_file)
                
                with open(file_path, 'r') as file:
                    products_data = json.load(file)
                    
                    # If the JSON contains a single product
                    if isinstance(products_data, dict):
                        products_data = [products_data]
                    
                    # Add unique _id to each product if not present
                    for product in products_data:
                        if '_id' not in product:
                            product['_id'] = str(uuid.uuid4())
                    
                    # Insert products into MongoDB
                    result = db.products.insert_many(products_data)
                    
            return jsonify({'message': 'Products inserted successfully'}), 200
            
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    def get_products(self):
        # Get all products from the database
        category = request.args.get("category")
        query = {"category": category} if category else {}
        products = list(db.products.find(query))
        return jsonify(products)
    
    def get_product_id(self, product_id):
        product = db.products.find_one({"_id": product_id})
        if product:
            product["_id"] = str(product["_id"])
            return jsonify(product)
        return jsonify({"error": "Product not found"}), 404
    
    def search_products(self):
        query = request.args.get("q", "")  # Get the search query from URL parameter
        if not query:
            return jsonify({"error": "No search query provided"}), 400

        # Perform a case-insensitive search on the product name
        results = list(db.products.find(
            {"title": {"$regex": query, "$options": "i"}},
            {"_id": 1, "title": 1, "price": 1, "link": 1, "category": 1}  # Include relevant fields
        ))

        # Convert ObjectId to string for JSON serialization
        for product in results:
            product["_id"] = str(product["_id"])

        return jsonify(results)