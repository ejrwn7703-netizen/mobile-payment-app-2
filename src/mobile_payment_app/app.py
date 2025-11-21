from flask import Flask, jsonify
from .routes import bp as api_bp
from .auth_routes import auth_bp
from dotenv import load_dotenv
import os

# .env 파일 로드
load_dotenv()

app = Flask(__name__, static_folder="static")
app.register_blueprint(api_bp)
app.register_blueprint(auth_bp)


@app.route("/", methods=["GET"])
def index():
    return jsonify(message="Welcome to the Mobile Payment App", 
                   endpoints={
                       "scan": "/scan",
                       "checkout": "/checkout",
                       "api_health": "/api/health",
                       "api_scan": "/api/scan (POST)",
                       "api_products": "/api/products (GET)",
                       "auth_signup": "/api/auth/signup (POST)",
                       "auth_login": "/api/auth/login (POST)",
                       "auth_me": "/api/auth/me (GET)"
                   })


@app.route("/scan", methods=["GET"])
def scan_page():
    """바코드 스캔 페이지"""
    return app.send_static_file('scan.html')


@app.route("/checkout", methods=["GET"])
def checkout():
    # Serve the static checkout page for demo
    return app.send_static_file('checkout.html')


@app.route("/payments/complete", methods=["GET"])
def payments_complete():
    # Serve the static completion page when user is redirected back from mock provider
    return app.send_static_file('complete.html')

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)

