import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from wiki_cli.context import WikiConfig
from wiki_cli.checking import audit_filenames, audit_internal_links


class TestChecking(unittest.TestCase):
    def test_audit_filenames_validation(self) -> None:
        """Test auditing of filenames for lowercase kebab-case naming standard."""
        with TemporaryDirectory() as tmpdir:
            config = WikiConfig(wiki_dir=tmpdir)
            
            # Create valid and invalid files
            valid_path = Path(tmpdir) / "valid-kebab-case.md"
            invalid_path = Path(tmpdir) / "Invalid_Name.md"
            
            valid_path.write_text("content", encoding="utf-8")
            invalid_path.write_text("content", encoding="utf-8")
            
            warnings = audit_filenames(config)
            self.assertEqual(len(warnings), 1)
            self.assertIn("Filename 'Invalid_Name.md' is not lowercase kebab-case.", warnings[0])

    def test_audit_internal_links_validation(self) -> None:
        """Test auditing of internal link structures (WikiLinks and Markdown links)."""
        with TemporaryDirectory() as tmpdir:
            config = WikiConfig(wiki_dir=tmpdir)
            
            # Create one target file
            target_path = Path(tmpdir) / "target-page.md"
            target_path.write_text("content", encoding="utf-8")
            
            # Create a source file with both valid and broken links
            source_content = """---
id: wiki:source
type: Person
---
Here is a valid WikiLink [[target-page]] and a broken WikiLink [[non-existent-page]].
And a valid Markdown link [Target](target-page.md) and a broken Markdown link [Broken](missing.md).
"""
            source_path = Path(tmpdir) / "source-page.md"
            source_path.write_text(source_content, encoding="utf-8")
            
            warnings = audit_internal_links(config)
            
            # Verify exactly the two broken links are reported
            self.assertEqual(len(warnings), 2)
            self.assertTrue(any("Broken WikiLink [[non-existent-page]]" in w for w in warnings))
            self.assertTrue(any("Broken Markdown link [missing.md]" in w for w in warnings))


if __name__ == "__main__":
    unittest.main()
