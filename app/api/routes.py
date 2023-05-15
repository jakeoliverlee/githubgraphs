# myflaskapp/api/routes.py
from flask import Blueprint, jsonify, request
from app.services.github import (fetch_commit_count_per_day, plot_commit_count)

api = Blueprint('api', __name__)

@api.route('/v1/commit-graph', methods=['GET'])
def get_commit_graph():
    username = request.args.get('username', default = None, type = str)
    if username:
        commit_graph = generate_github_commit_graph(username)
        return jsonify(commit_graph)
    else:
        return jsonify({"message": "username parameter is required"}), 400
