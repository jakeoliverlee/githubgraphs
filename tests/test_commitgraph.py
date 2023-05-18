from main import app
from flask import json
import unittest


class FlaskTestCase(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.client = self.app.test_client()
