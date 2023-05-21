import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import unittest
from unittest.mock import patch
from flask import json
from main import app
from app.services.commitgraph import (
    RepoNotFoundError,
    NoCommitsFoundError,
    InvalidUsername,
)


class TestCommitGraphAPI(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()

    def test_no_username_or_repo(self):
        response = self.client.get("/v1/commit-graph")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["detail"], "username&repo parameter is required")

    def test_no_repo(self):
        response = self.client.get("/v1/commit-graph?username=test")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["detail"], "repo parameter is required")

    def test_invalid_theme(self):
        response = self.client.get(
            "/v1/commit-graph?username=test&repo=test&theme=invalid_theme"
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "invalid theme, please choose from the available themes", data["detail"]
        )

    def test_invalid_period(self):
        response = self.client.get(
            "/v1/commit-graph?username=test&repo=test&period=invalid_period"
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn(
            "invalid period, please choose from the available periods", data["detail"]
        )

    @patch(
        "app.services.commitgraph.fetch_commit_count_per_day",
        side_effect=RepoNotFoundError("repo not found"),
    )
    def test_repo_not_found(self, _):
        response = self.client.get("/v1/commit-graph?username=test&repo=test")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["detail"], "Repository test/test not found.")

    @patch(
        "app.services.commitgraph.fetch_commit_count_per_day",
        side_effect=InvalidUsername("invalid username"),
    )
    def test_invalid_username(self, _):
        response = self.client.get(
            "/v1/commit-graph?username=xvbfdfbvdfzbdbcvbdsfb&repo=test"
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["detail"], "Username does not exist on Github")


if __name__ == "__main__":
    unittest.main()
