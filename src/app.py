from flask import Flask
import random
import logging
import sys

app = Flask(__name__)

# Logs must go to stdout for K8s to see them
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)
app.logger.setLevel(logging.INFO)

@app.route('/')
def index():
    # Simulate 20% failure rate
    if random.random() < 0.2:
        app.logger.error("CRITICAL: Database Connection Timeout. Retrying...")
        return "Internal Server Error", 500

    app.logger.info("Transaction processed successfully.")
    return "OK", 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
