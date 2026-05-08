---
id: wiki:wiki-cli
type: SoftwareApplication
name: Wiki CLI
softwareVersion: 0.1.0
description: Command-line interface for querying, validating, and managing the semantic vault
---

# Wiki CLI

The Wiki CLI is the primary companion tool for authoring, validating, and querying this semantic knowledge vault. It parses markdown files, converts YAML/JSON frontmatter into RDF graphs, resolves blank nodes, and performs deductive reasoning under OWL-RL semantics.

Refer to [[wiki-workflows]] to get started with common writing workflows, or [[wiki-schema]] to learn about active shapes and validation standards.

## Subcommand reference

### 1. `wiki create`
Scaffolds a new markdown file with standardized semantic frontmatter.
```bash
wiki create "Gregory Smith"
```

### 2. `wiki check`
Runs unified audits against the active vault, including filename formatting (lowercase kebab-case) and link health.
```bash
# Run warnings and errors verbose
wiki check -v

# Run with strict mode (fails CI on warnings)
wiki check --strict
```

### 3. `wiki query`
Allows executing raw SPARQL SELECT or CONSTRUCT queries against your vault's unified graph.
```bash
wiki query "SELECT ?name WHERE { ?s schema:name ?name }"
```

### 4. `wiki render`
Finds any dynamic SPARQL query comments inside your markdown files and updates their tables inline.
```bash
wiki render -v
```

### 5. `wiki export`
Compiles all document frontmatter into a canonical JSON-LD array.
```bash
wiki export -o exported-wiki.json
```
