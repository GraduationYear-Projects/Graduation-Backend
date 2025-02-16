from flask import Flask, request, jsonify
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from safetensors.torch import load_file

app = Flask(__name__)

MODEL_NAME = "distilbert-base-uncased-finetuned-sst-2-english"
TOKENIZER = AutoTokenizer.from_pretrained(MODEL_NAME)

# Load the model
try:
    model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME)
    model.eval()
except Exception as e:
    print(f"Error loading model: {e}")
    raise

def predict_sentiment(text):
    """Analyze sentiment of given text and return Positive/Negative/Neutral"""
    inputs = TOKENIZER(text, return_tensors="pt", truncation=True, padding=True)
    with torch.no_grad():
        outputs = model(**inputs)
    logits = outputs.logits
    sentiment_index = torch.argmax(logits, dim=1).item()

    return "Positive" if sentiment_index == 1 else "Negative"

@app.route("/analyze_sentiment", methods=["POST"])
def analyze_sentiment():
    data = request.json
    text = data.get("text", "")

    if not text:
        return jsonify({"sentiment": "Neutral"})

    sentiment = predict_sentiment(text)
    return jsonify({"sentiment": sentiment})

if __name__ == "__main__":
    app.run(port=5002)