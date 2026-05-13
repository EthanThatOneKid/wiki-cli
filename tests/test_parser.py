import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from llm_wiki.parser import (
    parse_frontmatter,
    split_frontmatter_body,
    ensure_context,
)


class TestFrontmatter(unittest.TestCase):
    def test_parse_frontmatter_valid(self) -> None:
        """Test parsing valid YAML frontmatter."""
        content = """---
id: wiki:gregory
name: Gregory
type: Person
---
Hello World
"""
        data = parse_frontmatter(content)
        self.assertIsNotNone(data)
        self.assertEqual(data.get("id"), "wiki:gregory")
        self.assertEqual(data.get("type"), "Person")
        self.assertEqual(data.get("name"), "Gregory")

    def test_parse_frontmatter_json(self) -> None:
        """Test parsing valid JSON frontmatter."""
        content = """---
{
  "id": "wiki:gregory",
  "name": "Gregory",
  "type": "Person"
}
---
Hello World
"""
        data = parse_frontmatter(content)
        self.assertIsNotNone(data)
        self.assertEqual(data.get("id"), "wiki:gregory")
        self.assertEqual(data.get("type"), "Person")

    def test_parse_frontmatter_invalid(self) -> None:
        """Test parsing invalid/broken frontmatters."""
        # No frontmatter delimiter
        self.assertIsNone(parse_frontmatter("Hello World"))
        
        # Single delimiter without any body or ending
        self.assertIsNone(parse_frontmatter("---"))
        
        # Invalid YAML syntax
        self.assertIsNone(parse_frontmatter("---\n[invalid_yaml\n---"))
        
        # Invalid JSON syntax
        self.assertIsNone(parse_frontmatter("---\n{\n---"))
        
        # Non-dictionary parsed yaml
        self.assertIsNone(parse_frontmatter("---\n- item1\n- item2\n---"))

    def test_ensure_context(self) -> None:
        """Test ensure_context injects defaults."""
        # Missing context entirely
        data = {"name": "Gregory"}
        updated = ensure_context(data)
        self.assertIn("@context", updated)
        self.assertEqual(updated["@context"]["@vocab"], "https://schema.org/")
        
        # Partial existing context dict
        data_partial = {"@context": {"custom": "http://custom.org/"}}
        updated_partial = ensure_context(data_partial)
        self.assertEqual(updated_partial["@context"]["custom"], "http://custom.org/")
        self.assertEqual(updated_partial["@context"]["@vocab"], "https://schema.org/")
        
        # Scalar non-dict @context remains untouched
        data_scalar = {"@context": "schema.org"}
        updated_scalar = ensure_context(data_scalar)
        self.assertEqual(updated_scalar["@context"], "schema.org")


    def test_split_frontmatter_body(self) -> None:
        """Test split_frontmatter_body returns (frontmatter, body) correctly."""
        # Valid frontmatter
        content = """---
id: wiki:test
name: Test
---
Body text here"""
        data, body = split_frontmatter_body(content)
        self.assertIsNotNone(data)
        self.assertEqual(data["name"], "Test")
        self.assertEqual(body, "Body text here")

        # No frontmatter
        no_fm = "Just body text\nwith multiple lines"
        data, body = split_frontmatter_body(no_fm)
        self.assertIsNone(data)
        self.assertEqual(body, no_fm)

    def test_split_frontmatter_body_with_dashes_in_body(self) -> None:
        """Test split_frontmatter_body handles --- in body text."""
        content = """---
id: wiki:test
name: Test
---
Body with --- dashes --- in text"""
        data, body = split_frontmatter_body(content)
        self.assertIsNotNone(data)
        self.assertEqual(body, "Body with --- dashes --- in text")


if __name__ == "__main__":
    unittest.main()
