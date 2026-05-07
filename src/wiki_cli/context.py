"""Central Context managing CLI settings, paths, and namespace bindings."""

from __future__ import annotations

from pathlib import Path
from typing import Any
from rdflib import Namespace, RDF, RDFS, OWL
from rdflib.namespace import XSD

# Standard static namespaces
SCHEMA = Namespace("https://schema.org/")
WIKI = Namespace("https://book.etok.me/wiki/")
FOAF = Namespace("http://xmlns.com/foaf/0.1/")
DC = Namespace("http://purl.org/dc/elements/1.1/")
DCTERMS = Namespace("http://purl.org/dc/terms/")

DEFAULT_NAMESPACES = {
    "schema": SCHEMA,
    "wiki": WIKI,
    "foaf": FOAF,
    "rdf": RDF,
    "rdfs": RDFS,
    "xsd": XSD,
    "owl": OWL,
    "dc": DC,
    "dcterms": DCTERMS,
}


class Context:
    """Manages CLI configurations, directories, and namespace/prefix mappings."""

    def __init__(
        self,
        wiki_dir: str | Path = "wiki",
        shapes_dir: str | Path = "shapes",
        reasoning_dir: str | Path = "reasoning",
        raw_dir: str | Path = "raw",
        wiki_base: str = "https://book.etok.me/wiki/",
    ) -> None:
        self.wiki_dir = Path(wiki_dir)
        self.shapes_dir = Path(shapes_dir)
        self.reasoning_dir = Path(reasoning_dir)
        self.raw_dir = Path(raw_dir)
        self.wiki_base = wiki_base
        self.namespaces = dict(DEFAULT_NAMESPACES)

    def bind_namespaces(self, graph: Any) -> None:
        """Bind all managed namespaces to an RDFLib Graph instance."""
        for prefix, namespace in self.namespaces.items():
            graph.bind(prefix, namespace)
