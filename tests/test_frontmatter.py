import unittest
from wiki_cli.frontmatter import normalize_frontmatter_str, parse_frontmatter


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

    def test_normalize_frontmatter_standardizes_keys(self) -> None:
        """Test that frontmatter normalization standardizes property keys to camelCase."""
        content = """---
given_name: Gregory
family_name: Smith
type: Person
id: wiki:gregory
---
Body content here
"""
        normalized = normalize_frontmatter_str(content)
        
        # Verify snake_case converted to camelCase
        self.assertIn("givenName: Gregory", normalized)
        self.assertIn("familyName: Smith", normalized)
        # Verify --- boundaries are preserved
        self.assertTrue(normalized.startswith("---"))
        self.assertTrue(normalized.strip().endswith("Body content here"))


if __name__ == "__main__":
    unittest.main()
