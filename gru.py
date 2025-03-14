from flask import Flask, request, jsonify
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import tokenizer_from_json
import numpy as np
import json

app = Flask(__name__)

# Load the trained GRU model
model = load_model("gru.h5")

# Load the tokenizer from JSON
with open("gru_tokenizer.json", "r") as f:
    tokenizer_json = f.read()
    tokenizer = tokenizer_from_json(tokenizer_json)

# Define the label mapping
label_mapping = {0: "negative", 1: "neutral", 2: "positive"}

# Function to predict sentiment
def predict_sentiment(text):
    seq = tokenizer.texts_to_sequences([text])
    padded_seq = pad_sequences(seq, maxlen=200)
    prediction = model.predict(padded_seq)
    sentiment_class = prediction.argmax()
    sentiment_label = label_mapping[sentiment_class]
    confidence = float(max(prediction[0]))
    return sentiment_label, confidence

# API route for prediction
@app.route("/analyze_sentiment", methods=["POST"])
def predict():
    try:
        data = request.get_json()
        text = data.get("text", "")
        
        if not text:
            return jsonify({"error": "No text provided"}), 400

        sentiment, confidence = predict_sentiment(text)
        
        response = {
            "text": text,
            "sentiment": sentiment,
            "confidence": confidence
        }
        
        return jsonify(response)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Run the app
if __name__ == "__main__":
    app.run(port=5003, debug=True)
