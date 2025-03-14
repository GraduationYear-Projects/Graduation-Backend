from flask import Flask, request, jsonify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from pymongo import MongoClient

app = Flask(__name__)

# Use TF-IDF vectorizer instead of sentence-transformers
vectorizer = TfidfVectorizer(stop_words='english')

from app import db

def fetch_reviews(product_id):
    """Fetch reviews for a specific product from MongoDB."""
    reviews = db.reviews.find({"product_id": product_id}, {"comment": 1, "_id": 0})
    return [review["comment"] for review in reviews if "comment" in review]  # Use "comment" key


def save_summary(product_id, summary):
    """Delete old summary and save the new one in the reviews_summary collection."""
    db.reviews_summary.delete_many({"product_id": product_id})
    db.reviews_summary.insert_one({"product_id": product_id, "summary": summary})

def summarize_reviews(reviews):
    """Summarize all reviews using TF-IDF vectorization and cosine similarity."""
    if not reviews:
        return "No reviews available."
    
    # Create TF-IDF matrix
    tfidf_matrix = vectorizer.fit_transform(reviews)
    
    # Calculate the average TF-IDF vector
    avg_tfidf = np.mean(tfidf_matrix.toarray(), axis=0).reshape(1, -1)
    
    # Find the review closest to the average
    similarities = cosine_similarity(avg_tfidf, tfidf_matrix)[0]
    closest_idx = np.argmax(similarities)
    
    return reviews[closest_idx]  # Return the most representative review

@app.route("/update_summary", methods=["POST"])
def update_summary():
    """Fetch reviews, generate summary, and store in MongoDB."""
    try:
        data = request.get_json()
        product_id = data.get("product_id")
        
        if not product_id:
            return jsonify({"error": "No product_id provided"}), 400
        
        reviews = fetch_reviews(product_id)
        summary = summarize_reviews(reviews)
        save_summary(product_id, summary)
        
        return jsonify({"product_id": product_id, "summary": summary, "total_reviews": len(reviews)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/get_summary", methods=["GET"])
def get_summary():
    """Retrieve the summary of all reviews for a product from MongoDB."""
    try:
        product_id = request.args.get("product_id")
        
        if not product_id:
            return jsonify({"error": "No product_id provided"}), 400
        
        result = db.reviews_summary.find_one({"product_id": product_id}, {"summary": 1, "_id": 0})
        
        if result:
            return jsonify({"product_id": product_id, "summary": result["summary"]})
        else:
            return jsonify({"error": "No summary found for this product"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(port=5004, debug=True)
