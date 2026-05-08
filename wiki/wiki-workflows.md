---
id: wiki:wiki-workflows
type: TechArticle
name: Wiki workflows and authoring guide
about: wiki:wiki-cli
---

# Wiki workflows and authoring guide

This guide covers common editing, auditing, and publishing procedures for contributing to the semantic knowledge vault.

## Step 1: Create a new page

To scaffold a new page, run the `create` subcommand. It automatically converts the title to a clean kebab-case filename and generates a standardized YAML frontmatter block.

```bash
wiki create "My New Article"
```

## Step 2: Fill in the semantic metadata

Always check [[wiki-schema]] to see what fields are required for your document type. For example, if your page describes a person:

```yaml
---
id: wiki:alice-smith
type: schema:Person
name: Alice Smith
givenName: Alice
familyName: Smith
context: Software Engineer working on the Wiki CLI
status: permanent
dateCreated: 2026-05-08
---
```

## Step 3: Run the validation suite

Before committing any files, run `wiki check` to verify that all filenames are valid, all internal WikiLinks resolve correctly, and all SHACL constraints are satisfied.

```bash
wiki check -v
```

## Step 4: Render dynamic tables

If your page contains inline SPARQL query comments (`<!-- sparql:start -->`), run `wiki render` to update the markdown tables automatically:

```bash
wiki render -v
```
