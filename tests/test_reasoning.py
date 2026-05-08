import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from rdflib import Graph, URIRef, RDF, RDFS, Namespace

from wiki_cli.context import Context, WikiConfig
from wiki_cli.reasoning import load_axioms, apply_inference


class TestReasoning(unittest.TestCase):
    def test_load_axioms_and_apply_inference(self) -> None:
        """Test load_axioms parses custom TTL axioms and apply_inference extends graph with OWL-RL deductive closure."""
        with TemporaryDirectory() as tmpdir:
            reasoning_dir = Path(tmpdir)
            
            # Create a simple RDFS subClassOf axiom
            # Under standard semantics, if Person is subClassOf Agent, and Gregory is a Person,
            # then Gregory must be inferred as an Agent.
            axiom_content = """
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <https://schema.org/> .

schema:Person rdfs:subClassOf schema:Agent .
"""
            (reasoning_dir / "custom-axiom.ttl").write_text(axiom_content, encoding="utf-8")
            
            config = WikiConfig(reasoning_dir=reasoning_dir)
            graph = Graph()
            
            # Setup initial fact: Gregory is a Person
            schema = Namespace("https://schema.org/")
            gregory = URIRef("wiki:gregory")
            graph.add((gregory, RDF.type, schema.Person))
            
            # Verify gregory is NOT currently an Agent
            self.assertFalse((gregory, RDF.type, schema.Agent) in graph)
            
            # Load axioms and apply inference (passing WikiConfig as designed by CLI)
            apply_inference(graph, config)
            
            # Verify the class hierarchy was loaded and deductive closure derived gregory is an Agent
            self.assertTrue((gregory, RDF.type, schema.Agent) in graph)

    def test_load_axioms_non_existent_or_invalid(self) -> None:
        """Test load_axioms handles non-existent folders and invalid turtle files gracefully."""
        # Non-existent directory
        config_none = WikiConfig(reasoning_dir=Path("non-existent-folder"))
        graph_none = Graph()
        load_axioms(graph_none, config_none)
        self.assertEqual(len(graph_none), 0)
        
        # Invalid turtle syntax in directory
        with TemporaryDirectory() as tmpdir:
            invalid_ttl = Path(tmpdir) / "invalid.ttl"
            invalid_ttl.write_text("invalid turtle contents", encoding="utf-8")
            
            config_invalid = WikiConfig(reasoning_dir=tmpdir)
            graph_invalid = Graph()
            load_axioms(graph_invalid, config_invalid)
            self.assertEqual(len(graph_invalid), 0)


if __name__ == "__main__":
    unittest.main()
