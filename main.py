from flask import Flask
import connexion
import controller 

app = connexion.App(__name__, specification_dir="./")
app.add_api("swagger.yml")

if __name__ == "__main__":
    app.run(port=5000, debug=True)
