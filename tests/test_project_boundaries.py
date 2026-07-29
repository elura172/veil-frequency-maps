import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class ProjectBoundaryTests(unittest.TestCase):
    def test_generic_mcp_does_not_import_compositions(self):
        violations = []
        for source in (ROOT / "osc_mcp").glob("*.py"):
            text = source.read_text(encoding="utf-8")
            if "projects." in text or "projects/" in text:
                violations.append(source.name)
        self.assertEqual(violations, [])

    def test_each_project_has_a_specification_and_readme(self):
        projects = [path for path in (ROOT / "projects").iterdir()
                    if path.is_dir() and not path.name.startswith("_")]
        self.assertTrue(projects)
        for project in projects:
            self.assertTrue((project / "spec.py").is_file(), project.name)
            self.assertTrue((project / "README.md").is_file(), project.name)


if __name__ == "__main__":
    unittest.main()
