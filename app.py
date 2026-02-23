import os
import requests
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

def get_ai_response(user_message):
    url = "https://openrouter.ai/api/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "mistralai/mistral-7b-instruct",
        "messages": [
            {
                "role": "system",
                "content": "You are a college placement assistant. Answer only placement, exam, subject and staff related questions."
            },
            {"role": "user", "content": user_message}
        ]
    }

    response = requests.post(url, headers=headers, json=data)
    result = response.json()

    return result["choices"][0]["message"]["content"]

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/chat", methods=["POST"])
def chat():
    user_msg = request.json["message"]
    reply = get_ai_response(user_msg)
    return jsonify({"reply": reply})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
