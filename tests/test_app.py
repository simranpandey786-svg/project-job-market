import unittest
from app import app
from analysis import classify_title, words


class ClassificationTests(unittest.TestCase):
    def test_ai_category(self):
        self.assertEqual(classify_title("LLM engineer for RAG system"), "AI & Machine Learning")

    def test_legal_category(self):
        self.assertEqual(classify_title("Contract attorney needed"), "Legal")

    def test_stop_words_removed(self):
        self.assertNotIn("project", words("Python project for analytics"))


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_health(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["status"], "ok")

    def test_recommendations(self):
        response = self.client.get("/api/recommend?q=python&limit=3")
        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(response.json["count"], 3)
        self.assertIn("results", response.json)


if __name__ == "__main__":
    unittest.main()
