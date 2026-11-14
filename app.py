import os
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/")
def home():
    return """
    <h1>Giveaway Winner API</h1>
    <p>Backend is running.</p>
    """

@app.route("/health")
def health():
    return jsonify({
        "status": "ok",
        "application": "Giveaway Winner"
    })

@app.route("/callback")
def callback():
    return """
    <h1>Instagram connection callback</h1>
    <p>Callback endpoint is ready.</p>
    """

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
