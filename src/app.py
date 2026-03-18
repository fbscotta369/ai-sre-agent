from flask import Flask, jsonify
import random
import logging
import sys

app = Flask(__name__)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)


@app.route("/health")
def health():
    return jsonify({"status": "healthy"}), 200


@app.route("/ready")
def ready():
    return jsonify({"status": "ready"}), 200


@app.route("/")
def index():
    if random.random() < 0.2:
        app.logger.error("CRITICAL: Database Connection Timeout. Retrying...")
        return "Internal Server Error", 500

    app.logger.info("Transaction processed successfully.")
    return "OK", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
