"""SHACL validation logic using pyshacl against loaded constraint shapes."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional
from rdflib import Graph
import pyshacl

from .context import Context
from .frontmatter import frontmatter_from_path
from .rdf import frontmatter_to_graph

logger = logging.getLogger(__name__)


def load_shapes(context: Context) -> Graph:
    """Load all SHACL shapes (.ttl files) from shapes directory into a Graph."""
    shapes_graph = Graph()
    shapes_graph.bind("sh", "http://www.w3.org/ns/shacl#")
    shapes_graph.bind("schema", "https://schema.org/")

    if context.shapes_dir.exists():
        for shape_file in sorted(context.shapes_dir.glob("*.ttl")):
            try:
                shapes_graph.parse(shape_file, format="turtle")
            except Exception as e:
                logger.warning("Failed to parse shape file %s: %s", shape_file.name, e)

    return shapes_graph


def validate_file(file_path: Path, context: Context, verbose: bool = False) -> Optional[tuple[bool, str]]:
    """Validate a single markdown file's frontmatter against loaded shapes.

    Returns None if no frontmatter is found, otherwise returns (conforms, results_text).
    """
    data = frontmatter_from_path(file_path)
    if not data:
        return None

    shapes_graph = load_shapes(context)
    data_graph = frontmatter_to_graph(data, context, file_id=file_path.stem)

    conforms, _, results_text = pyshacl.validate(
        data_graph,
        shapes_graph,
        inference="rdfs",
    )

    return conforms, results_text


def validate_all(context: Context, verbose: bool = False) -> tuple[bool, str]:
    """Validate all wiki documents as a single unified Graph against loaded shapes."""
    shapes_graph = load_shapes(context)
    data_graph = Graph()
    context.bind_namespaces(data_graph)

    errors = []
    has_files = False

    if context.wiki_dir.exists():
        for md_file in sorted(context.wiki_dir.glob("*.md")):
            try:
                data = frontmatter_from_path(md_file)
                if data:
                    data_graph += frontmatter_to_graph(data, context, file_id=md_file.stem)
                    has_files = True
            except Exception as e:
                errors.append((md_file.name, str(e)))

    if not has_files:
        return True, "No markdown documents with frontmatter found to validate."

    conforms, _, results_text = pyshacl.validate(
        data_graph,
        shapes_graph,
        inference="rdfs",
        abort_on_first_error=False,
    )

    if errors:
        results_text += f"\nParse errors encountered ({len(errors)}):\n"
        for name, err in errors:
            results_text += f"  - {name}: {err}\n"

    return conforms, results_text


def validate_summary(context: Context) -> dict[str, Any]:
    """Perform a per-file SHACL validation and return a summary of conforming/failing/error files."""
    shapes_graph = load_shapes(context)
    results: dict[str, Any] = {"conforms": [], "fails": [], "errors": []}

    if context.wiki_dir.exists():
        for md_file in sorted(context.wiki_dir.glob("*.md")):
            try:
                data = frontmatter_from_path(md_file)
                if not data:
                    results["errors"].append({"file": md_file.name, "reason": "no frontmatter"})
                    continue

                data_graph = frontmatter_to_graph(data, context, file_id=md_file.stem)
                conforms, _, _ = pyshacl.validate(data_graph, shapes_graph, inference="rdfs")

                if conforms:
                    results["conforms"].append(md_file.name)
                else:
                    results["fails"].append(md_file.name)
            except Exception as e:
                results["errors"].append({"file": md_file.name, "reason": str(e)})

    return results
