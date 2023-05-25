import os
from flask import Flask
import connexion
import controller
from werkzeug.middleware.profiler import ProfilerMiddleware


app = connexion.App(__name__, specification_dir="./")
app_dir = os.path.dirname(os.path.realpath(__file__))  # path to the directory of the script
swagger_file = os.path.join(app_dir, "swagger.yml")  # path to swagger.yml
app.add_api(swagger_file)

# profile_app = app.app
# profile_app.config['PROFILE'] = True
# profile_app.wsgi_app = ProfilerMiddleware(profile_app.wsgi_app, restrictions=[30])

if __name__ == "__main__":
    app.run(port=5000, debug=True)
