from flask import Flask, jsonify
from .routes import bp as api_bp

app = Flask(__name__, static_folder="static")
app.register_blueprint(api_bp)


@app.route("/payments/complete", methods=["GET"])
def payments_complete():
    # Serve the static completion page when user is redirected back from mock provider
    return app.send_static_file('complete.html')

@app.route("/checkout", methods=["GET"])
def checkout():
    # Serve the static checkout page for demo
    return app.send_static_file('checkout.html')

@app.route("/", methods=["GET"])
def index():
    return jsonify(message="Welcome to the Mobile Payment App")

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)

