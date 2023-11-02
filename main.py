import os
from flask import Flask
import connexion
import controller
from werkzeug.middleware.profiler import ProfilerMiddleware
from flask_cors import CORS

# Initialize Connexion app
connexion_app = connexion.App(__name__, specification_dir="./")

# Get the underlying Flask app
app = connexion_app.app

# Enable CORS
CORS(app)

# Specify the path to your swagger.yml file
app_dir = os.path.dirname(os.path.realpath(__file__))
swagger_file = os.path.join(app_dir, "swagger.yml")

# Add the API to your Connexion app
connexion_app.add_api(swagger_file)

if __name__ == "__main__":
    connexion_app.run(port=5000, debug=True)
