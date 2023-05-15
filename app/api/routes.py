from flask import Blueprint, jsonify, request, send_file, current_app
from app.services.commitgraph import (
    fetch_commit_count_per_day,
    plot_commit_count,
    RepoNotFoundError,
    NoCommitsFoundError,
    InvalidUsername,
    THEMES,
    TYPES,
)


api = Blueprint("api", __name__)


@api.route("/v1/commit-graph", methods=["GET"])
def get_commit_graph():
    username = request.args.get("username", default=None, type=str)
    repo = request.args.get("repo", default=None, type=str)
    type = request.args.get("type", default=None, type=str)
    theme = request.args.get("theme", default=None, type=str)
    if username:
        try:
            if not repo:
                return (
                    jsonify(
                        {"message": "repo parameter is required", "status_code": 400}
                    ),
                    400,
                )
            if theme:
                if theme not in THEMES:
                    theme_names = ", ".join(THEMES.keys())

                    return (
                        jsonify(
                            {
                                "message": f"invalid theme, please choose from the available themes: {theme_names}",
                                "status_code": 400,
                            }
                        ),
                        400,
                    )
            if type:
                if type not in TYPES:
                    types_list = [i for i in TYPES]
                    return (
                        jsonify(
                            {
                                "message": f"invalid type, please choose from the available types: {types_list}",
                                "status_code": 400,
                            }
                        ),
                        400,
                    )

            try:
                commit_count = fetch_commit_count_per_day(username, repo)
                if type == "png":
                    plot_commit_count(
                        commit_count, f"{repo}_commit_graph.png", repo, "png", theme
                    )
                    return send_file(f"{repo}_commit_graph.png", mimetype="image/png")
                else:  # Default to SVG if type is not specified or not "png"
                    plot_commit_count(
                        commit_count, f"{repo}_commit_graph.svg", repo, "svg", theme
                    )
                    return send_file(
                        f"{repo}_commit_graph.svg", mimetype="image/svg+xml"
                    )

            except RepoNotFoundError as e:
                return jsonify({"message": str(e), "status_code": 404}), 404
            except NoCommitsFoundError as e:
                return jsonify({"message": str(e), "status_code": 400}), 400
            except ValueError or TypeError as e:
                return jsonify({"message": str(e), "status_code": 400}), 400
        except InvalidUsername as e:
            return jsonify({"message": str(e), "status_code": 400}), 400

    else:
        return (
            jsonify(
                {"message": "username&repo parameter is required", "status_code": 400}
            ),
            400,
        )
