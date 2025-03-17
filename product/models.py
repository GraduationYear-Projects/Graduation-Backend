from flask import Flask, jsonify, request, session, redirect
from app import db
import uuid
import json
import os
from datetime import datetime, timezone
import requests
import logging

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
            # Ensure _id is a string
            product["_id"] = str(product["_id"])
            
            # Debug log
            print(f"Product found: {product_id}")
            print(f"Product data: {product}")
            
            # Ensure link field exists
            if "link" not in product or not product["link"]:
                print(f"Warning: Product {product_id} has no image link")
                # Set a default image URL that's stored locally in the frontend
                # The frontend will handle this by using its local placeholder
                product["link"] = ""
            
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

    
    def analyze_sentiment(self, text):
        SENTIMENT_MODEL_URL = "http://localhost:5003/analyze_sentiment"

        """Send review text to the sentiment model and return prediction."""
        response = requests.post(SENTIMENT_MODEL_URL, json={"text": text})
        
        if response.status_code == 200:
            return response.json().get("sentiment", "Neutral")  # Default to Neutral if error
        return "Neutral"
    
    def add_review(self):
        data = request.json
        if not all(key in data for key in ("product_id", "user_id", "rating", "comment")):
            return jsonify({"error": "Missing required fields"}), 400

        sentiment = self.analyze_sentiment(data["comment"])

        review = {
            "_id": uuid.uuid4().hex,
            "product_id": data["product_id"],
            "user_id": data["user_id"],
            "rating": data["rating"],
            "comment": data["comment"],
            "sentiment": sentiment,
            "timestamp": datetime.now(timezone.utc)
        }

        db.reviews.insert_one(review)
        return jsonify({"message": "Review added with sentiment analysis", "sentiment": sentiment}), 200
    
    def get_reviews(self, product_id):
        reviews = list(db.reviews.find(
            {"product_id": product_id},
            {"_id": 0}  # Exclude MongoDB's _id field
        ))
        return jsonify(reviews)
        
    def get_reviews_summary(self, product_id):
        """Get the summary of reviews for a specific product."""
        try:
            # Call the summarization service
            SUMMARY_SERVICE_URL = "http://localhost:5004/get_summary"
            print(f"Calling summarization service at {SUMMARY_SERVICE_URL} for product {product_id}")
            
            response = requests.get(SUMMARY_SERVICE_URL, params={"product_id": product_id}, timeout=10)
            print(f"Response status: {response.status_code}")
            print(f"Response content: {response.text}")
            
            if response.status_code == 200:
                return jsonify(response.json())
            elif response.status_code == 404:
                return jsonify({"message": "No summary found for this product. Try updating the summary first."}), 404
            else:
                return jsonify({"error": f"Error from summary service: {response.json().get('error')}"}), response.status_code
                
        except Exception as e:
            logging.error(f"Error getting review summary: {str(e)}")
            return jsonify({"error": str(e)}), 500
    
    def update_reviews_summary(self, product_id):
        """Update the summary of reviews for a specific product."""
        try:
            # Call the summarization service to update the summary
            SUMMARY_UPDATE_URL = "http://localhost:5004/update_summary"
            response = requests.post(SUMMARY_UPDATE_URL, json={"product_id": product_id})
            
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({"error": f"Error from summary service: {response.json().get('error')}"}), response.status_code
                
        except Exception as e:
            logging.error(f"Error updating review summary: {str(e)}")
            return jsonify({"error": str(e)}), 500