"""OWL-RL deductive reasoning expansion and custom axiom loading."""

from __future__ import annotations

import logging
from rdflib import Graph
import owlrl

from .context import Context

logger = logging.getLogger(__name__)


def load_axioms(graph: Graph, context: Context) -> None:
    """Load custom OWL/RDFS axioms from configured reasoning directory."""
    if context.reasoning_dir.exists():
        for ttl_file in sorted(context.reasoning_dir.glob("*.ttl")):
            try:
                graph.parse(ttl_file, format="turtle")
            except Exception as e:
                logger.warning("Failed to parse axiom file %s: %s", ttl_file.name, e)


def apply_inference(graph: Graph, context: Context) -> Graph:
    """Load axioms and apply OWL-RL deductive closure reasoning to the graph."""
    load_axioms(graph, context)
    try:
        owlrl.DeductiveClosure(owlrl.OWLRL_Semantics).expand(graph)
    except Exception as e:
        logger.error("Failed to apply OWL-RL reasoning: %s", e)
    return graph
