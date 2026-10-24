from flask import Flask
from users import users_bp
from admin import admin_bp

app = Flask(__name__)

app.register_blueprint(users_bp, url_prefix="/users")
app.register_blueprint(admin_bp, url_prefix="/admin")

@app.route("/")
def index():
    return "Hello, World!"

if __name__ == "__main__":
    app.run(debug=True, port=5001)