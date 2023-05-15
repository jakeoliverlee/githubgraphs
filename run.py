# run.py
from flask import Flask
from app.api.routes import api as api_blueprint
from app import config

app = Flask(__name__)
app.register_blueprint(api_blueprint, url_prefix="/api")

if __name__ == "__main__":
    app.run(debug=True)
