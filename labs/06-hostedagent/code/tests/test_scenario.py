from pathlib import Path
import sys
import os
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SOURCE = ROOT.parents[1] / "00-getting-started"


class ScenarioTests(unittest.TestCase):
    def setUp(self):
        from fastapi.testclient import TestClient
        from web import app
        self.client = TestClient(app)

    def test_top_navigation_links_to_scenario_and_repository(self):
        html = self.client.get("/").text
        self.assertIn('href="/scenario"', html)
        self.assertIn("CJ 전자 시나리오", html)
        self.assertIn('href="https://github.com/ChangJu-Ahn/microsoft-iq-series-kr"', html)

    def test_scenario_page_and_source_are_public_and_preserve_readme(self):
        page = self.client.get("/scenario")
        self.assertEqual(200, page.status_code)
        self.assertIn("CJ 전자 시나리오", page.text)
        self.assertIn("질문하러 가기", page.text)
        response = self.client.get("/scenario/content")
        self.assertEqual(200, response.status_code)
        self.assertEqual((SOURCE / "README.md").read_text(), response.text)

    def test_only_declared_diagram_assets_are_served(self):
        for name in ("customer-problem.svg", "problem-solving-workshop.svg"):
            response = self.client.get("/scenario/assets/" + name)
            self.assertEqual(200, response.status_code)
            self.assertEqual((SOURCE / "assets" / name).read_bytes(), response.content)
        self.assertEqual(404, self.client.get("/scenario/assets/.env").status_code)
        self.assertEqual(404, self.client.get("/scenario/assets/customer-problem.excalidraw").status_code)

    def test_web_image_contains_exact_readme_and_its_diagrams(self):
        from deploy_web import build_context
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            build_context(target)
            self.assertEqual((SOURCE / "README.md").read_bytes(),
                             (target / "scenario-content/README.md").read_bytes())
            self.assertEqual(
                {"customer-problem.svg", "problem-solving-workshop.svg"},
                {p.name for p in (target / "scenario-content/assets").iterdir()},
            )

    def test_container_content_directory_does_not_depend_on_repo_depth(self):
        source = (ROOT / "scenario.py").read_text()
        namespace = {"__file__": "/app/scenario.py"}
        with tempfile.TemporaryDirectory() as temp:
            with patch.dict(os.environ, {"SCENARIO_CONTENT_DIR": temp}):
                exec(compile(source, "/app/scenario.py", "exec"), namespace)
                self.assertEqual(Path(temp).resolve(), namespace["content_directory"]())


if __name__ == "__main__":
    unittest.main()
