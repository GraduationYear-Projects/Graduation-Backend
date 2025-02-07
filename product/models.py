from flask import Flask, jsonify, request, session, redirect
from app import db
import uuid
import json
import os

class Product:
    
    def insert_products_from_json(self, json_folder_path='product/json'):
        """
        Insert products from JSON files in the specified folder into MongoDB
        """
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
        """
        Get all products from the database
        """
        products = db.products.find({})
        return list(products)
    