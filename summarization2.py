from flask import Flask, request, jsonify
from transformers import pipeline, AutoTokenizer, AutoModelForSeq2SeqLM
from collections import defaultdict
import re
from datetime import datetime
from pymongo import MongoClient
from app import db
app = Flask(__name__)

# Collections
reviews_collection = db["reviews"]
summary_collection = db["reviews_summary"]

# Initialize the NLP models
def initialize_models():
    # Load tokenizer and model once
    tokenizer = AutoTokenizer.from_pretrained("t5-small")
    model = AutoModelForSeq2SeqLM.from_pretrained("t5-small")
    
    # For text summarization
    summarizer = pipeline("summarization", model=model, tokenizer=tokenizer)
    
    return summarizer, tokenizer, model

# Global models
summarizer, tokenizer, model = initialize_models()

# Improved feature extraction function
def extract_features(reviews):
    # Common mobile phone features to look for
    feature_keywords = [
        "battery", "camera", "display", "screen", "performance", "speed", 
        "storage", "memory", "design", "size", "weight", "price", 
        "processor", "speaker", "audio", "fingerprint", "face recognition",
        "charging", "durability", "water resistance", "software", "os",
        "user interface", "wifi", "bluetooth", "signal", "reception"
    ]
    
    # Dictionary to store features and their sentiments
    features = defaultdict(list)
    
    # Process each review
    for review in reviews:
        text = review.lower()
        
        # Check for each feature
        for feature in feature_keywords:
            # Find sentences containing the feature
            # First split by periods, then look for feature mentions
            sentences = text.split('.')
            for sentence in sentences:
                if feature in sentence:
                    # Extract sentiment for this feature in this sentence
                    
                    # Common positive adjectives
                    positive_adj = ["good", "great", "excellent", "amazing", "impressive", 
                                   "fantastic", "outstanding", "exceptional", "brilliant",
                                   "wonderful", "superb", "beautiful", "vibrant", "bright",
                                   "crisp", "clear", "fast", "quick", "smooth", "reliable",
                                   "perfect", "flawless", "premium"]
                    
                    # Common negative adjectives
                    negative_adj = ["bad", "poor", "terrible", "awful", "disappointing",
                                    "mediocre", "subpar", "slow", "laggy", "unreliable",
                                    "small", "tiny", "limited", "insufficient", "inadequate",
                                    "short", "weak", "dim", "dull", "blurry", "fuzzy",
                                    "defective", "buggy", "problematic", "hot"]
                    
                    # Common neutral adjectives
                    neutral_adj = ["average", "decent", "okay", "ok", "moderate", "standard",
                                  "normal", "typical", "basic", "simple", "regular"]
                    
                    # Check for adjectives near the feature
                    found_sentiment = False
                    
                    # Check for positive adjectives
                    for adj in positive_adj:
                        if adj in sentence:
                            features[feature].append(adj)
                            found_sentiment = True
                            break
                    
                    # If no positive adjective, check for negative ones
                    if not found_sentiment:
                        for adj in negative_adj:
                            if adj in sentence:
                                features[feature].append(adj)
                                found_sentiment = True
                                break
                    
                    # If still no sentiment, check for neutral ones
                    if not found_sentiment:
                        for adj in neutral_adj:
                            if adj in sentence:
                                features[feature].append(adj)
                                found_sentiment = True
                                break
                    
                    # Special case for storage size
                    if feature == "storage" and "too small" in sentence or "filled up quickly" in sentence:
                        features[feature].append("small")
                        found_sentiment = True
                    
                    # If we found a sentiment, move to next feature
                    if found_sentiment:
                        break
    
    # Process features to get majority sentiment
    feature_summary = {}
    for feature, sentiments in features.items():
        if sentiments:
            # Use the most common sentiment
            sentiment_counts = defaultdict(int)
            for s in sentiments:
                sentiment_counts[s] += 1
            
            most_common_sentiment = max(sentiment_counts.items(), key=lambda x: x[1])[0]
            feature_summary[feature] = most_common_sentiment
    
    return feature_summary

# Generate text summary
def generate_text_summary(reviews):
    if not reviews:
        return "No reviews available."
    
    # Combine all reviews into one text
    combined_text = " ".join(reviews)
    
    # If the text is too long, chunk it
    if len(combined_text) > 1000:
        combined_text = combined_text[:1000]
    
    # Generate summary
    try:
        summary = summarizer(combined_text, max_length=100, min_length=30, do_sample=False)[0]['summary_text']
        return summary
    except Exception as e:
        print(f"Error in summarization: {e}")
        return "Failed to generate summary."

# API endpoint to get summary for a product
@app.route("/get_summary", methods=["GET"])
def get_summary():
    product_id = request.args.get("product_id")
    
    if not product_id:
        return jsonify({"error": "product_id parameter is required"}), 400
    
    # Check if we already have a summary
    existing_summary = summary_collection.find_one({"product_id": product_id})
    if existing_summary:
        if "_id" in existing_summary:
            existing_summary["_id"] = str(existing_summary["_id"])
        return jsonify(existing_summary)
    
    # If no summary exists, return an error - must call update_summary first
    return jsonify({"error": "No summary exists for this product. Please use update_summary endpoint first."}), 404

# API endpoint to update summary for a product
@app.route("/update_summary", methods=["POST"])
def update_summary():
    data = request.get_json()
    
    if not data or "product_id" not in data:
        return jsonify({"error": "Invalid request. 'product_id' field is required."}), 400
    
    product_id = data.get("product_id")
    
    # Fetch all comments for this product from the reviews collection
    reviews_cursor = reviews_collection.find({"product_id": product_id})
    comments = [doc["comment"] for doc in reviews_cursor]
    
    if not comments:
        return jsonify({"error": "No reviews found for this product"}), 404
    
    # Extract features and generate summary
    feature_summary = extract_features(comments)
    text_summary = generate_text_summary(comments)
    
    # Create the summary object
    summary = {
        "product_id": product_id,
        "text_summary": text_summary,
        "features": feature_summary,
        "total_reviews": len(comments),
        "last_updated": datetime.now()
    }
    
    # Save to MongoDB (upsert: create or update)
    summary_collection.update_one(
        {"product_id": product_id}, 
        {"$set": summary},
        upsert=True
    )
    
    # Return without MongoDB-specific fields
    if "_id" in summary:
        del summary["_id"]
        
    return jsonify({"status": "Success", "summary": summary}), 200

if __name__ == "__main__":
    app.run(port=5004, debug=True)