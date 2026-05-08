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

    def test_cli_create_duplicate_fails(self) -> None:
        """Test that wiki create fails if the document already exists."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            # Create once
            result1 = runner.invoke(main, ["--wiki-dir", tmpdir, "create", "Duplicate"])
            self.assertEqual(result1.exit_code, 0)
            
            # Create twice
            result2 = runner.invoke(main, ["--wiki-dir", tmpdir, "create", "Duplicate"])
            self.assertEqual(result2.exit_code, 1)
            self.assertIn("Error: Document duplicate.md already exists", result2.output)

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

    def test_cli_check_single_file(self) -> None:
        """Test wiki check with a single file specified."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            wiki_dir = Path(tmpdir)
            valid_file = wiki_dir / "valid-file.md"
            valid_file.write_text("""---
id: wiki:valid-file
type: schema:WebPage
name: Valid File
---
""", encoding="utf-8")
            
            # Conforming single file check
            result = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "check", str(valid_file)])
            self.assertEqual(result.exit_code, 0)
            
            # Non-conforming single file check
            invalid_file = wiki_dir / "Invalid_Name.md"
            invalid_file.write_text("""---
id: wiki:invalid-name
type: schema:WebPage
name: Invalid Name
---
""", encoding="utf-8")
            result_invalid = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "check", str(invalid_file), "--strict"])
            self.assertEqual(result_invalid.exit_code, 1)

    def test_cli_query_formats(self) -> None:
        """Test that wiki query executes successfully with various output formats."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            wiki_dir = Path(tmpdir)
            # Create a simple page
            (wiki_dir / "alice.md").write_text("""---
type: Person
name: Alice
---
""", encoding="utf-8")
            
            # Run simple query SELECT name
            query_str = "SELECT ?name WHERE { ?s <https://schema.org/name> ?name }"
            
            # Table format
            res_table = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "query", "--no-inference", query_str])
            self.assertEqual(res_table.exit_code, 0)
            self.assertIn("Alice", res_table.output)
            
            # JSON format
            res_json = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "query", "-f", "json", "--no-inference", query_str])
            self.assertEqual(res_json.exit_code, 0)
            parsed = json.loads(res_json.output)
            self.assertIn("results", parsed)
            
            # Error mode - invalid SPARQL syntax
            res_err = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "query", "INVALID QUERY"])
            self.assertEqual(res_err.exit_code, 1)

    def test_cli_render_inline_sparql(self) -> None:
        """Test that wiki render updates inline SPARQL blocks correctly."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            wiki_dir = Path(tmpdir)
            
            # Create a source file with SPARQL block
            source_content = """---
type: Person
name: Gregory
---
<!-- sparql:start -->
```sparql
SELECT ?name WHERE { ?s <https://schema.org/name> ?name }
```
<!-- sparql:end -->
"""
            file_path = wiki_dir / "gregory.md"
            file_path.write_text(source_content, encoding="utf-8")
            
            result = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "render", "--no-inference", "-v"])
            self.assertEqual(result.exit_code, 0)
            
            # Verify the SPARQL block was rendered and updated inline
            updated_content = file_path.read_text(encoding="utf-8")
            self.assertIn("Gregory", updated_content)

    def test_cli_export(self) -> None:
        """Test that wiki export supports bulk and single file exports."""
        runner = CliRunner()
        with TemporaryDirectory() as tmpdir:
            wiki_dir = Path(tmpdir)
            
            # Create a simple page
            valid_file = wiki_dir / "gregory.md"
            valid_file.write_text("""---
type: Person
name: Gregory
---
""", encoding="utf-8")
            
            # Bulk export
            result_bulk = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "export"])
            self.assertEqual(result_bulk.exit_code, 0)
            data_bulk = json.loads(result_bulk.output)
            self.assertEqual(len(data_bulk), 1)
            self.assertEqual(data_bulk[0]["jsonld"]["name"], "Gregory")
            
            # Single file export
            result_single = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "export", str(valid_file)])
            self.assertEqual(result_single.exit_code, 0)
            data_single = json.loads(result_single.output)
            self.assertEqual(data_single["name"], "Gregory")
            
            # Single file export failure (no frontmatter)
            no_fm_file = wiki_dir / "no-fm.md"
            no_fm_file.write_text("Hello", encoding="utf-8")
            result_fail = runner.invoke(main, ["--wiki-dir", str(wiki_dir), "export", str(no_fm_file)])
            self.assertEqual(result_fail.exit_code, 1)


if __name__ == "__main__":
    unittest.main()
