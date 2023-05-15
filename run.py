from flask import Flask
from app.api.routes import api

app = Flask(__name__)

# Register the api Blueprint
app.register_blueprint(api)

if __name__ == "__main__":
    app.run(debug=True)
