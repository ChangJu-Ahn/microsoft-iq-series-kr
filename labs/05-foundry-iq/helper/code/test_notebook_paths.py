import ast
from contextlib import chdir
import json
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[4]
LABS = [ROOT / "labs" / name for name in [
    "03-web-iq", "04-work-iq", "05-foundry-iq",
]]


class NotebookPathTests(unittest.TestCase):
    def helper_from(self, directory):
        notebook = LABS[2] / "kb_retrieve_test.ipynb"
        cells = json.loads(notebook.read_text())["cells"]
        source = "".join(next(
            cell["source"] for cell in cells if cell.get("id") == "v2-trace-setup"
        ))
        assignment = next(
            node for node in ast.parse(source).body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "helper_dir"
                    for target in node.targets)
        )
        namespace = {"Path": Path}
        with chdir(directory):
            exec(compile(ast.Module(body=[assignment], type_ignores=[]),
                         str(notebook), "exec"), namespace)
        return namespace["helper_dir"]

    def test_trace_helper_discovery_from_repository_root(self):
        self.assertEqual(self.helper_from(ROOT), LABS[2] / "helper" / "code")

    def test_trace_helper_discovery_from_foundry_lab(self):
        self.assertEqual(self.helper_from(LABS[2]), LABS[2] / "helper" / "code")

    def check_links(self, path, text):
        for link in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", text):
            if link.startswith(("http:", "https:", "mailto:", "#")):
                continue
            with self.subTest(file=str(path.relative_to(ROOT)), link=link):
                self.assertTrue((path.parent / link.split("#")[0]).exists(),
                                f"연결 대상이 없습니다: {path.name} → {link}")

    def test_local_links_in_relocated_notebooks(self):
        for lab in LABS:
            for path in lab.glob("*.ipynb"):
                notebook = json.loads(path.read_text())
                for cell in notebook["cells"]:
                    if cell["cell_type"] == "markdown":
                        self.check_links(path, "".join(cell["source"]))

    def test_local_links_in_lab_guides_and_scenario_references(self):
        paths = [ROOT / "labs/00-getting-started/README.md"]
        paths.extend(path for lab in LABS for path in lab.glob("*.md"))
        for path in paths:
            self.check_links(path, path.read_text())


if __name__ == "__main__":
    unittest.main()
