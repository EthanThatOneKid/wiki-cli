# LLM Wiki CLI 🚀

An elegant, pure, and idiomatic Python command-line interface for managing a semantic knowledge base of markdown documents with SHACL validation and SPARQL reasoning.

## Key features
- **Modern Packaging**: Configured cleanly with standard `pyproject.toml` optimized for `uv` or `pip`.
- **Pure Click CLI**: Subcommands mapped elegantly (`validate`, `query`, `render`, `frontmatter`).
- **Flexible Frontmatter Parsing**: Supports YAML and JSON frontmatter blocks with standard triple-dash `---` boundaries.
- **Context-Centric**: Simplifies namespace, prefix mappings, and settings in a single coherent `Context` class matching JSON-LD `@context`.
- **Deductive Reasoning**: Full OWL-RL deductive reasoning expansion powered by `owlrl`.
- **SHACL Validation**: Rich conformance testing of markdown files against loaded shapes powered by `pyshacl` with JSON and text reporting.
- **Dynamic SPARQL Rendering**: Scan and execute embedded SPARQL query blocks in markdown files, injecting updated results back into the documents inline.

## Installation

Install the package and its dependencies using `uv` (recommended) or `pip`:

```bash
# Using uv (fastest)
uv pip install -e .

# Using standard pip
pip install -e .
```

## Subcommand guide

### `validate`
Validate the entire wiki or a single file against SHACL shapes loaded from `shapes/`.

```bash
# Validate all documents in the wiki
wiki validate

# Validate a single document file
wiki validate wiki/gregory.md

# Output per-file summary (conforming, fails, errors)
wiki validate --summary

# Output formatted as JSON
wiki validate --summary --format json
```

### `query`
Execute any SPARQL SELECT or CONSTRUCT query against the loaded and reasoning-expanded RDF graph.

```bash
# Execute direct query string and output as ASCII table
wiki query "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"

# Query and output as Turtle (for CONSTRUCT queries)
wiki query "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }" -f turtle

# Run query from stdin and write results to a file
cat my_query.sparql | wiki query -f markdown -o results.md
```

### `render`
Identify all embedded SPARQL blocks in your markdown files, run their queries against the reasoning-expanded RDF graph, and replace the outputs inline. Under the "silence is golden" Unix philosophy, this command exits silently with code 0 upon success.

```bash
# Render silently (default)
wiki render

# Render with verbose summary output
wiki render -v
```

An embedded SPARQL block is defined in your markdown files like this:
````html
<!-- sparql:start -->
```sparql
SELECT ?name ?email WHERE {
  ?person a schema:Person ;
          schema:name ?name ;
          schema:email ?email .
}
```

| Name | Email |
| --- | --- |
| Gregory | gregory@example.com |
<!-- sparql:end -->
````

### `frontmatter`
Utilities to normalize or convert metadata blocks. Under the "silence is golden" Unix philosophy, `normalize` exits silently with code 0 upon success.

```bash
# Normalize and standardize property casings silently (default)
wiki frontmatter normalize

# Normalize and print a summary of changes
wiki frontmatter normalize -v

# Dry-run normalization to preview changes (always prints)
wiki frontmatter normalize --dry-run

# Convert frontmatter blocks to canonical JSON-LD array
wiki frontmatter jsonld -o wiki.jsonld
```

### Printing and piping (Unix filters)
Following the Unix philosophy of pipes and filters, `wiki` works seamlessly with native system utilities. Outputs from query execution or document inspection can be easily formatted and spooled directly to your printer.

#### On Unix/macOS
* **Format and Print a Document:**
  Use `pr` to add headers, margins, and page numbers before sending to `lp`:
  ```bash
  cat wiki/gregory.md | pr -h "Gregory Document" | lp
  ```
* **Format and Print Query Results:**
  Run a query and print its tabular results:
  ```bash
  wiki query "SELECT ?s ?p WHERE { ?s ?p ?o }" | pr -h "SPARQL Graph Query" | lp
  ```

#### On Windows (PowerShell)
* **Print a Document:**
  ```powershell
  Get-Content wiki/gregory.md | Out-Printer
  ```
* **Print Query Results:**
  ```powershell
  wiki query "SELECT ?s ?p WHERE { ?s ?p ?o }" | Out-Printer
  ```

## Domain glossary and decisions
To understand the domain terminology (such as **Wiki**, **Document**, **Context**, **Validation**, and **Shape**), please refer to:
*   [CONTEXT.md](CONTEXT.md) — Glossary and Domain Model mapping.
*   [0001-context-centric-configuration.md](docs/adr/0001-context-centric-configuration.md) — Architectural Decision Record (ADR) on context naming.
*   [0002-userland-printing.md](docs/adr/0002-userland-printing.md) — Architectural Decision Record (ADR) on adopting userland printing filters.

