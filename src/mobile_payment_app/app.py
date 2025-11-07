# ...existing code...
from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return jsonify(message="Welcome to the Mobile Payment App")

# 추가 라우트는 여기서 정의하세요.

if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=8000)
# ...existing code...

