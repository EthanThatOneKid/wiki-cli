# Silence is golden default behavior

## Context

The Unix philosophy suggests that successful commands should be silent by default ("silence is golden"). In previous iterations, action-oriented subcommands (such as `render` and `frontmatter normalize`) printed verbose success summaries and status information directly to `stdout`.

While this output can be helpful for interactive use, it violates Unix-style execution expectations, cluttering output and making commands less suitable for automated scripting, CI/CD pipelines, or piping and filtering without redirection or custom filters.

## Decision

We decided to **adopt the "silence is golden" philosophy** by changing the default behavior for action-oriented commands (`render` and `frontmatter normalize`) to exit silently with code 0 upon success. 

To preserve the ability to inspect details and summaries during interactive use, we introduced a standard `-v`/`--verbose` flag to these commands. Explicit preview modes (like `--dry-run`) still print outputs by default, as the user explicitly asked to preview the changes.

## Consequences

### Positive
* **Idiomatic Unix Design**: Commands exit silently upon success by default, adhering to long-standing Unix standards.
* **Pipeline-Friendly**: Subcommands are easier to script and run in automated workflows or CI/CD pipelines without generating unnecessary noise in log files.
* **Interactive Flexibility**: Users can opt-in to detailed action feedback anytime using the `-v` or `--verbose` flag.

### Negative
* Interactive users must append `-v` or `--verbose` to see a success message (e.g., `Successfully updated X files...`).
