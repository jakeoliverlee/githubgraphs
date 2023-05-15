from flask import Blueprint, jsonify, request, send_file, current_app
from app.services.commitgraph import fetch_commit_count_per_day, plot_commit_count

api = Blueprint("api", __name__)


# http://example/v1/commit-graph?username={username}&repo={repo}&type={svg|png}
@api.route("/v1/commit-graph", methods=["GET"])
def get_commit_graph():
    username = request.args.get("username", default=None, type=str)
    repo = request.args.get("repo", default=None, type=str)
    type = request.args.get("type", default=None, type=str)
    if username:
        try:
            commit_count = fetch_commit_count_per_day(username, repo)
            if type == "png":
                plot_commit_count(commit_count, f"{repo}_commit_graph.png", repo, "png")
                return send_file(f"{repo}_commit_graph.png", mimetype="image/png")
            else:  # Default to SVG if type is not specified or not "png"
                plot_commit_count(commit_count, f"{repo}_commit_graph.svg", repo, "svg")
                return send_file(f"{repo}_commit_graph.svg", mimetype="image/svg+xml")

        except ValueError as e:
            return jsonify({"message": str(e)}), 404
    else:
        return jsonify({"message": "username parameter is required"}), 400
