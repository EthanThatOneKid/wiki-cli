import unittest
from pathlib import Path
from rdflib import Graph, URIRef, RDF, Literal

from wiki_cli.context import WikiConfig, Context
from wiki_cli.rdf import frontmatter_to_graph


class TestRDFFrontmatter(unittest.TestCase):
    def setUp(self) -> None:
        self.config = WikiConfig()
        self.context = self.config.context

    def test_nested_dict_creates_blank_node(self) -> None:
        """Test that a nested dictionary without explicit @type creates a blank node."""
        data = {
            "@type": "Person",
            "@id": "wiki:gregory",
            "name": "Gregory",
            "address": {
                "street": "123 Main St",
                "city": "Seattle"
            }
        }
        graph = frontmatter_to_graph(data, self.context)
        
        # Verify subject
        subject = URIRef("wiki:gregory")

        
        # Verify name predicate
        name_pred = self.context.namespaces["schema"]["name"]
        self.assertTrue((subject, name_pred, Literal("Gregory")) in graph)
        
        # Verify address predicate points to a blank node
        address_pred = self.context.namespaces["schema"]["address"]
        blank_nodes = list(graph.objects(subject, address_pred))
        self.assertEqual(len(blank_nodes), 1)
        blank = blank_nodes[0]
        self.assertTrue(isinstance(blank, URIRef) and str(blank).startswith("_:blank"))
        
        # Verify properties on the blank node
        street_pred = self.context.namespaces["schema"]["street"]
        city_pred = self.context.namespaces["schema"]["city"]
        self.assertTrue((blank, street_pred, Literal("123 Main St")) in graph)
        self.assertTrue((blank, city_pred, Literal("Seattle")) in graph)

    def test_nested_typed_dict_creates_typed_blank_node(self) -> None:
        """Test that a nested dictionary with @type creates a typed blank node."""
        data = {
            "@type": "Person",
            "@id": "wiki:gregory",
            "name": "Gregory",
            "address": {
                "@type": "PostalAddress",
                "street": "123 Main St"
            }
        }
        graph = frontmatter_to_graph(data, self.context)
        subject = URIRef("wiki:gregory")
        address_pred = self.context.namespaces["schema"]["address"]
        blank = list(graph.objects(subject, address_pred))[0]
        
        type_pred = RDF.type
        expected_type = self.context.namespaces["schema"]["PostalAddress"]
        self.assertTrue((blank, type_pred, expected_type) in graph)

    def test_nested_referenced_dict_creates_uri_ref(self) -> None:
        """Test that a nested dictionary with @id maps directly to a URI reference."""
        data = {
            "@type": "Person",
            "@id": "wiki:gregory",
            "name": "Gregory",
            "spouse": {
                "@id": "wiki:bella"
            }
        }
        graph = frontmatter_to_graph(data, self.context)
        subject = URIRef("wiki:gregory")
        spouse_pred = self.context.namespaces["schema"]["spouse"]
        spouse_obj = list(graph.objects(subject, spouse_pred))[0]
        
        expected_spouse = URIRef(self.context.namespaces["wiki"]["bella"])
        self.assertEqual(spouse_obj, expected_spouse)

    def test_nested_list_of_dicts_creates_multiple_nodes(self) -> None:
        """Test that a list of nested dictionaries creates corresponding multiple blank nodes."""
        data = {
            "@type": "Person",
            "@id": "wiki:gregory",
            "address": [
                {"street": "123 Main St"},
                {"street": "456 Oak Ave"}
            ]
        }
        graph = frontmatter_to_graph(data, self.context)
        subject = URIRef("wiki:gregory")
        address_pred = self.context.namespaces["schema"]["address"]
        blanks = list(graph.objects(subject, address_pred))
        self.assertEqual(len(blanks), 2)
        
        street_pred = self.context.namespaces["schema"]["street"]
        streets = {str(graph.value(blank, street_pred)) for blank in blanks}
        self.assertEqual(streets, {"123 Main St", "456 Oak Ave"})

    def test_auto_inject_markdown_body(self) -> None:
        """Test that the markdown body is auto-injected into the graph if content_predicate is set."""
        data = {
            "@type": "Person",
            "@id": "wiki:gregory",
            "name": "Gregory"
        }
        self.config.content_predicate = "schema:text"
        body_text = "Gregory is a software engineer."
        
        graph = frontmatter_to_graph(data, self.config, body=body_text)
        subject = URIRef("wiki:gregory")
        
        text_pred = self.context.namespaces["schema"]["text"]
        self.assertTrue((subject, text_pred, Literal(body_text)) in graph)


if __name__ == "__main__":
    unittest.main()


