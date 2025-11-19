from flask import Flask, jsonify
from .routes import bp as api_bp

app = Flask(__name__)
app.config.from_object('config.Config')  # Load configuration from config.py
app.register_blueprint(api_bp)

@app.route("/", methods=["GET"])
def index():
    return jsonify(message="Welcome to the Mobile Payment App")

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)