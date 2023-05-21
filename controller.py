from flask import request, jsonify, send_file
from app.services.commitgraph import (
    fetch_commit_count_per_day,
    plot_commit_count,
    RepoNotFoundError,
    NoCommitsFoundError,
    InvalidUsername,
    THEMES,
    PERIODS,
)
from io import BytesIO

def get_commit_graph():
    username = request.args.get("username", default=None, type=str)
    repo = request.args.get("repo", default=None, type=str)
    period = request.args.get("period", default="month", type=str)
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
            if theme and theme not in THEMES:
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
            if period and period not in PERIODS:
                periods = [i for i in PERIODS]
                return (
                    jsonify(
                        {
                            "message": f"invalid period, please choose from the available periods : {periods}",
                            "status_code": 400,
                        }
                    ),
                    400,
                )

            commit_count = fetch_commit_count_per_day(username, repo, period)
            img_io = BytesIO()
            plot_commit_count(commit_count, img_io, repo, theme, period)
            img_io.seek(0)

            return send_file(img_io, mimetype="image/svg+xml")

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
