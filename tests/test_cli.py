import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from click.testing import CliRunner

from wiki_cli.__main__ import main


class TestCLI(unittest.TestCase):
    def test_cli_create_scaffolds_file(self) -> None:
        """Test that wiki create scaffolds a new document with standardized frontmatter."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            # Run "wiki create" pointing to our temporary directory
            result = runner.invoke(
                main,
                [
                    "--wiki-dir", tmpdir,
                    "create", "My New Document",
                    "-v"
                ]
            )
            self.assertEqual(result.exit_code, 0)
            self.assertIn("Created document my-new-document.md", result.output)
            
            # Verify file exists and has correct content
            file_path = Path(tmpdir) / "my-new-document.md"
            self.assertTrue(file_path.exists())
            
            content = file_path.read_text(encoding="utf-8")
            self.assertIn("id: wiki:my-new-document", content)
            self.assertIn("type: schema:WebPage", content)
            self.assertIn("name: My New Document", content)
            self.assertIn("# My New Document", content)

    def test_cli_check_succeeds_and_fails(self) -> None:
        """Test that wiki check succeeds on valid documents and fails on violations."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            # 1. Running check on empty directory conforms silently (success)
            result = runner.invoke(main, ["--wiki-dir", tmpdir, "check"])
            self.assertEqual(result.exit_code, 0)
            self.assertEqual(result.output, "")
            
            # 2. Add an invalid filename and test that strict mode fails
            invalid_file = Path(tmpdir) / "Invalid_Name.md"
            invalid_file.write_text("""---
id: wiki:invalid
type: schema:WebPage
name: Invalid Page
---
""", encoding="utf-8")
            
            result_strict = runner.invoke(main, ["--wiki-dir", tmpdir, "check", "--strict", "-v"])
            self.assertEqual(result_strict.exit_code, 1)
            self.assertIn("Errors:", result_strict.output)
            self.assertIn("is not lowercase kebab-case", result_strict.output)

    def test_cli_export_outputs_jsonld(self) -> None:
        """Test that wiki export compiles frontmatter into canonical JSON-LD arrays."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            # Create a simple valid page
            valid_file = Path(tmpdir) / "gregory.md"
            valid_file.write_text("""---
id: wiki:gregory
type: Person
name: Gregory
---
""", encoding="utf-8")
            
            result = runner.invoke(main, ["--wiki-dir", tmpdir, "export"])
            self.assertEqual(result.exit_code, 0)
            
            # Parse outputs as JSON
            data = json.loads(result.output)
            self.assertEqual(len(data), 1)
            self.assertEqual(data[0]["file"], "gregory.md")
            self.assertEqual(data[0]["jsonld"]["name"], "Gregory")


if __name__ == "__main__":
    unittest.main()
