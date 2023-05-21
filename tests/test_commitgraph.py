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
        self.assertEqual(data["detail"], "Missing query parameter 'username'")

    def test_no_repo(self):
        response = self.client.get("/v1/commit-graph?username=test")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["detail"], "Missing query parameter 'repo'")

    def test_invalid_theme(self):
        response = self.client.get(
            "/v1/commit-graph?username=test&repo=test&theme=invalid_theme"
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("is not one of ['dark', 'light', 'sunset', 'forest', 'ocean', 'sakura', 'monochrome', 'rainbow']", data["detail"])

    def test_invalid_period(self):
        response = self.client.get(
            "/v1/commit-graph?username=test&repo=test&period=invalid_period"
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertIn("is not one of ['month', 'year', 'all']", data["detail"])

    @patch(
        "app.services.commitgraph.fetch_commit_count_per_day",
        side_effect=RepoNotFoundError("Repository test/test not found."),
    )
    def test_repo_not_found(self, mock_fetch):
        response = self.client.get("/v1/commit-graph?username=test&repo=test")
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(data["message"], "Repository test/test not found.")

    @patch(
        "app.services.commitgraph.check_valid_user_and_repo",
        side_effect=InvalidUsername("Username does not exist on Github"),
    )
    def test_invalid_username(self, mock_fetch):
        response = self.client.get(
            "https://jakeoliverlee-githubgraphs.nw.r.appspot.com/v1/commit-graph?username=xvbfdfbvdfzbdbcvbdsfb&repo=test"
        )
        data = json.loads(response.data)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(data["message"], "Username does not exist on Github")


if __name__ == "__main__":
    unittest.main()
