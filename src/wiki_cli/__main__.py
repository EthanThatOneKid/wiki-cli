"""Click CLI entrypoint defining subcommands and option handling."""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional
import click

from .context import Context
from .frontmatter import normalize_all, normalize_frontmatter_str, frontmatter_from_path
from .rdf import load_graph, graph_stats
from .reasoning import apply_inference
from .validation import validate_all, validate_file, validate_summary


def table_format(result: Any) -> str:
    """Format SPARQL SELECT results as a simple ASCII table."""
    rows = list(result)
    if not rows:
        return "(no results)"

    try:
        keys = [str(v) for v in result.vars]
    except Exception:
        keys = []

    if not keys and rows:
        first = rows[0]
        if isinstance(first, tuple):
            keys = [f"?v{i}" for i in range(len(first))]
        elif hasattr(first, "keys"):
            keys = list(first.keys())
        else:
            return str(rows)

    if not keys:
        return "(empty query)"

    col_widths = [len(str(k)) for k in keys]
    for row in rows:
        if isinstance(row, tuple):
            vals = [str(v) for v in row]
        else:
            vals = [str(row.get(k, "")) for k in keys]
        for i, val in enumerate(vals):
            if i < len(col_widths):
                col_widths[i] = max(col_widths[i], len(val))

    header = " | ".join(str(k).ljust(col_widths[i]) for i, k in enumerate(keys))
    sep = "-+-".join("-" * w for w in col_widths)
    lines = [header, sep]
    for row in rows:
        if isinstance(row, tuple):
            vals = [str(v) for v in row]
        else:
            vals = [str(row.get(k, "")) for k in keys]
        line = " | ".join(
            vals[i].ljust(col_widths[i]) if i < len(vals) else "" for i in range(len(keys))
        )
        lines.append(line)

    return "\n".join(lines)


def markdown_format(result: Any) -> str:
    """Format SPARQL SELECT results as a GitHub Flavored Markdown table."""
    rows = list(result)
    if not rows:
        return "(no results)"

    try:
        keys = [str(v) for v in result.vars]
    except Exception:
        keys = []

    if not keys and rows:
        first = rows[0]
        if isinstance(first, tuple):
            keys = [f"v{i}" for i in range(len(first))]
        elif hasattr(first, "keys"):
            keys = list(first.keys())
        else:
            return str(rows)

    if not keys:
        return "(empty query)"

    headers = [k.capitalize() for k in keys]
    header_line = "| " + " | ".join(headers) + " |"
    divider_line = "| " + " | ".join(["---"] * len(keys)) + " |"

    lines = [header_line, divider_line]
    for row in rows:
        if isinstance(row, tuple):
            vals = []
            for v in row:
                if v is None:
                    vals.append("")
                else:
                    s = str(v)
                    match = re.search(r"https://(?:book\.etok\.me|EthanThatOneKid\.github\.io/book)/wiki/([^/]+)\.md", s)
                    if match:
                        s = f"[[{match.group(1)}]]"
                    vals.append(s)
        else:
            vals = []
            for k in keys:
                v = row.get(k)
                if v is None:
                    vals.append("")
                else:
                    s = str(v)
                    match = re.search(r"https://(?:book\.etok\.me|EthanThatOneKid\.github\.io/book)/wiki/([^/]+)\.md", s)
                    if match:
                        s = f"[[{match.group(1)}]]"
                    vals.append(s)
        lines.append("| " + " | ".join(vals) + " |")

    return "\n".join(lines)


def run_query(graph: Any, query: str, output_format: str = "table") -> str:
    """Run a SPARQL SELECT or CONSTRUCT query against the graph, returning formatted output."""
    q = query.strip().upper()
    is_construct = q.startswith("CONSTRUCT") or q.startswith("DESCRIBE")

    if is_construct:
        result = graph.query(query)
        if output_format in ("turtle", "nt", "n3"):
            return result.serialize(format=output_format)
        return result.serialize(format="turtle")

    result = graph.query(query)

    if output_format == "json":
        return result.serialize(format="json").decode("utf-8")
    elif output_format == "csv":
        return result.serialize(format="csv").decode("utf-8")
    elif output_format == "tsv":
        return result.serialize(format="tsv").decode("utf-8")
    elif output_format in ("markdown", "md"):
        return markdown_format(result)
    else:
        return table_format(result)


# Matches the starting comment, query inside, and ending comment block with SPARQL inside
SPARQL_BLOCK_REGEX = re.compile(
    r"<!--\s*sparql:start\s*-->\s*```sparql\s*(.*?)\s*```\s*(.*?)\s*<!--\s*sparql:end\s*-->",
    re.DOTALL | re.IGNORECASE
)


def render_markdown_files(wiki_dir: Path, graph: Any) -> int:
    """Iterate over all markdown files, parse and replace dynamic SPARQL sections inline."""
    count = 0
    for md_file in wiki_dir.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        modified = False

        def replacer(match: re.Match) -> str:
            nonlocal modified
            query = match.group(1).strip()
            try:
                rendered_markdown = run_query(graph, query, output_format="markdown")
                modified = True
                return f"<!-- sparql:start -->\n```sparql\n{query}\n```\n\n{rendered_markdown}\n<!-- sparql:end -->"
            except Exception as e:
                click.echo(f"Error rendering query in {md_file.name}: {e}", err=True)
                return str(match.group(0))

        new_content = SPARQL_BLOCK_REGEX.sub(replacer, content)
        if modified and new_content != content:
            md_file.write_text(new_content, encoding="utf-8")
            count += 1

    return count


@click.group()
@click.option("--wiki-dir", default="wiki", help="Directory containing wiki markdown files.")
@click.option("--shapes-dir", default="shapes", help="Directory containing SHACL shape files.")
@click.option("--reasoning-dir", default="reasoning", help="Directory containing OWL/RDFS axioms.")
@click.option("--raw-dir", default="raw", help="Directory containing raw markdown files.")
@click.pass_context
def main(ctx: click.Context, wiki_dir: str, shapes_dir: str, reasoning_dir: str, raw_dir: str) -> None:
    """Query, validate, and manage your semantic LLM wiki."""
    ctx.obj = Context(
        wiki_dir=wiki_dir,
        shapes_dir=shapes_dir,
        reasoning_dir=reasoning_dir,
        raw_dir=raw_dir,
    )


@main.command()
@click.argument("file", required=False, type=click.Path(exists=True, path_type=Path))
@click.option("-v", "--verbose", is_flag=True, help="Print full validation report.")
@click.option("--summary", is_flag=True, help="Print per-file conformance summary.")
@click.option("--format", type=click.Choice(["text", "json"]), default="text", help="Output format.")
@click.option("--no-inference", is_flag=True, help="Skip loading reasoning axioms.")
@click.pass_obj
def validate(context: Context, file: Optional[Path], verbose: bool, summary: bool, format: str, no_inference: bool) -> None:
    """Validate wiki documents against SHACL shapes."""
    if file:
        result = validate_file(file, context, verbose=verbose)
        if result is None:
            click.echo("No frontmatter found in file.", err=True)
            sys.exit(1)
        conforms, text = result
        if format == "json":
            click.echo(json.dumps({"file": file.name, "conforms": conforms}))
        else:
            click.echo(f"[{'PASS' if conforms else 'FAIL'}] {file.name}")
            if verbose or not conforms:
                click.echo(text)
        sys.exit(0 if conforms else 1)

    if summary:
        results = validate_summary(context)
        if format == "json":
            click.echo(json.dumps(results, indent=2))
        else:
            total = len(results["conforms"]) + len(results["fails"]) + len(results["errors"])
            click.echo(f"Validated: {total} files")
            click.echo(f"Conforms:  {len(results['conforms'])}")
            click.echo(f"Fails:     {len(results['fails'])}")
            click.echo(f"Errors:    {len(results['errors'])}")
            if results["fails"]:
                click.echo("\nFailing files:")
                for name in results["fails"]:
                    click.echo(f"  - {name}")
            if results["errors"]:
                click.echo("\nError files:")
                for e in results["errors"]:
                    click.echo(f"  - {e['file']}: {e['reason']}")
        sys.exit(1 if results["fails"] or results["errors"] else 0)

    conforms, text = validate_all(context, verbose=verbose)
    if format == "json":
        click.echo(json.dumps({"conforms": conforms}))
    else:
        click.echo(f"[{'PASS' if conforms else 'FAIL'}] SHACL validation")
        if verbose or not conforms:
            click.echo(text)
    sys.exit(0 if conforms else 1)


@main.command()
@click.argument("query_args", nargs=-1, required=False)
@click.option("-f", "--format", "output_format", type=click.Choice(["table", "json", "csv", "tsv", "turtle", "n3", "markdown", "md"]), default="table")
@click.option("-o", "--output", type=click.Path(path_type=Path), help="Write output to specified file.")
@click.option("--no-inference", is_flag=True, help="Skip OWL-RL inference.")
@click.option("-v", "--verbose", is_flag=True, help="Print graph statistics before query results.")
@click.pass_obj
def query(context: Context, query_args: tuple[str, ...], output_format: str, output: Optional[Path], no_inference: bool, verbose: bool) -> None:
    """Run a SPARQL SELECT or CONSTRUCT query."""
    if query_args:
        sparql_query = " ".join(query_args)
    elif not sys.stdin.isatty():
        sparql_query = sys.stdin.read()
    else:
        click.echo("Error: No query provided.", err=True)
        sys.exit(1)

    graph = load_graph(context, infer=not no_inference)

    if verbose:
        stats = graph_stats(graph)
        click.echo(f"Graph stats: {stats['triples']} triples, {stats['subjects']} subjects\n")

    try:
        result = run_query(graph, sparql_query, output_format=output_format)
        if output:
            output.write_text(result, encoding="utf-8")
            click.echo(f"Written results to {output}")
        else:
            click.echo(result)
    except Exception as e:
        click.echo(f"Query Execution Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--no-inference", is_flag=True, help="Skip OWL-RL inference.")
@click.pass_obj
def render(context: Context, no_inference: bool) -> None:
    """Render inline SPARQL blocks in markdown files."""
    graph = load_graph(context, infer=not no_inference)
    count = render_markdown_files(context.wiki_dir, graph)
    click.echo(f"Successfully updated {count} markdown files with rendered SPARQL outputs.")


@main.command("print")
@click.argument("file", required=False, type=click.Path(exists=True, path_type=Path))
@click.option("-p", "--printer", help="Name of the printer to use.")
@click.option("--list", "list_printers", is_flag=True, help="List available printers.")
@click.option("--all", "print_all", is_flag=True, help="Print all documents in the wiki.")
@click.option("--no-frontmatter", is_flag=True, help="Strip frontmatter from markdown files before printing.")
@click.option("--query", "sparql_query", help="Run a SPARQL query and print its results.")
@click.option("--no-inference", is_flag=True, help="Skip OWL-RL inference when running a query.")
@click.option("--font-family", default="Segoe UI", help="Font family to use for printing.")
@click.option("--font-size", type=int, default=12, help="Font size (in points) to use for printing.")
@click.pass_obj
def print_cmd(
    context: Context,
    file: Optional[Path],
    printer: Optional[str],
    list_printers: bool,
    print_all: bool,
    no_frontmatter: bool,
    sparql_query: Optional[str],
    no_inference: bool,
    font_family: str,
    font_size: int,
) -> None:
    """Print wiki documents or SPARQL query results using a local or Wi-Fi printer."""
    # Get available printers
    printers = []
    try:
        ps_cmd = "Get-CimInstance Win32_Printer | Select-Object Name, Default | ConvertTo-Json"
        res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True, check=True)
        if res.stdout.strip():
            data = json.loads(res.stdout)
            printers = [data] if isinstance(data, dict) else data
    except Exception as e:
        click.echo(f"Error listing printers: {e}", err=True)

    if list_printers:
        click.echo("Available Printers:")
        for p in printers:
            default_marker = " [DEFAULT]" if p.get("Default") else ""
            click.echo(f"  - {p.get('Name')}{default_marker}")
        return

    # Determine which printer to use
    selected_printer = printer
    if not selected_printer:
        for p in printers:
            if p.get("Default"):
                selected_printer = p.get("Name")
                break
        if not selected_printer and printers:
            selected_printer = printers[0].get("Name")

    if not selected_printer:
        click.echo("Error: No printers found or specified.", err=True)
        sys.exit(1)

    # Function to send text to the printer
    def send_to_printer(text: str, title: str) -> None:
        click.echo(f"Sending '{title}' to printer '{selected_printer}' using {font_family} {font_size}pt...")
        temp_dir = Path("temp_print")
        temp_dir.mkdir(exist_ok=True)
        temp_file = temp_dir / "print_job.txt"
        ps_script_file = temp_dir / "run_print.ps1"
        try:
            temp_file.write_text(text, encoding="utf-8")
            
            ps_script = f"""
Add-Type -AssemblyName System.Drawing

$doc = New-Object System.Drawing.Printing.PrintDocument
$doc.PrinterSettings.PrinterName = '{selected_printer}'

$text = Get-Content -Raw -Encoding utf8 '{temp_file.absolute()}'
$font = New-Object System.Drawing.Font('{font_family}', {font_size})
$brush = [System.Drawing.Brushes]::Black

# Split text into lines cleanly
$global:lines = $text -split "\\r?\\n"
$global:lineIndex = 0

$doc.add_PrintPage({{
    param($sender, $e)
    
    $marginBounds = $e.MarginBounds
    $leftMargin = $marginBounds.Left
    $topMargin = $marginBounds.Top
    $width = $marginBounds.Width
    $y = $topMargin
    
    while ($global:lineIndex -lt $global:lines.Count) {{
        $line = $global:lines[$global:lineIndex]
        if ($line.Trim() -eq "") {{
            $y += $font.GetHeight($e.Graphics)
            $global:lineIndex++
            continue
        }}
        
        # Measure wrapped height
        $size = $e.Graphics.MeasureString($line, $font, $width)
        $height = $size.Height
        
        # Check if paragraph fits on current page
        if ($y + $height -gt $marginBounds.Bottom) {{
            $e.HasMorePages = $true
            return
        }}
        
        # Draw wrapped text inside rectangle
        $rect = New-Object System.Drawing.RectangleF($leftMargin, $y, $width, $height)
        $e.Graphics.DrawString($line, $font, $brush, $rect)
        
        $y += $height
        $global:lineIndex++
    }}
    
    $e.HasMorePages = $false
}})

$doc.Print()
"""
            ps_script_file.write_text(ps_script, encoding="utf-8")
            subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps_script_file.absolute())],
                capture_output=True,
                text=True,
                check=True
            )
            click.echo("Successfully sent to printer!")
        except Exception as e:
            click.echo(f"Failed to print '{title}': {e}", err=True)
            sys.exit(1)
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass
            if ps_script_file.exists():
                try:
                    ps_script_file.unlink()
                except Exception:
                    pass
            try:
                temp_dir.rmdir()
            except Exception:
                pass

    # Handle SPARQL query printing
    if sparql_query:
        graph = load_graph(context, infer=not no_inference)
        try:
            result = run_query(graph, sparql_query, output_format="table")
            send_to_printer(result, f"SPARQL Query: {sparql_query}")
            return
        except Exception as e:
            click.echo(f"Query Execution Error: {e}", err=True)
            sys.exit(1)

    # Clean markdown content helper
    def prepare_content(path: Path) -> str:
        content = path.read_text(encoding="utf-8")
        if no_frontmatter and content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content

    # Handle single file printing
    if file:
        content = prepare_content(file)
        send_to_printer(content, file.name)
        return

    # Handle all files printing
    if print_all:
        if not context.wiki_dir.exists():
            click.echo(f"Error: Wiki directory '{context.wiki_dir}' does not exist.", err=True)
            sys.exit(1)

        files = sorted(context.wiki_dir.glob("*.md"))
        if not files:
            click.echo("No documents found to print.", err=True)
            return

        for f in files:
            content = prepare_content(f)
            send_to_printer(content, f.name)
        return

    click.echo("Error: Must specify a file to print, use --all, use --query, or use --list.", err=True)
    sys.exit(1)


@main.group()
def frontmatter() -> None:
    """Utilities for normalizing and converting frontmatter."""
    pass


@frontmatter.command("normalize")
@click.argument("file", required=False, type=click.Path(exists=True, path_type=Path))
@click.option("--dry-run", is_flag=True, help="Print count of changes without writing them.")
@click.option("--standardize/--no-standardize", default=True, help="Standardize property key casing to camelCase.")
@click.pass_obj
def normalize(context: Context, file: Optional[Path], dry_run: bool, standardize: bool) -> None:
    """Normalize and format document frontmatter blocks."""
    if file:
        original = file.read_text(encoding="utf-8")
        normalized = normalize_frontmatter_str(original, standardize_keys=standardize)
        if normalized != original:
            if not dry_run:
                file.write_text(normalized, encoding="utf-8")
                click.echo(f"Normalized frontmatter in {file.name}")
            else:
                click.echo(f"[DRY-RUN] Would normalize frontmatter in {file.name}")
        else:
            click.echo(f"Frontmatter in {file.name} is already normalized.")
        sys.exit(0)

    results = normalize_all(context.wiki_dir, standardize_keys=standardize, dry_run=dry_run)
    if dry_run:
        click.echo(f"[DRY-RUN] Would fix {results['fixed']} files, skipped {results['skipped']}")
    else:
        click.echo(f"Normalized frontmatter in {results['fixed']} files, skipped {results['skipped']}")
    sys.exit(0)


@frontmatter.command("jsonld")
@click.argument("file", required=False, type=click.Path(exists=True, path_type=Path))
@click.option("-o", "--output", type=click.Path(path_type=Path), help="File to write canonical JSON-LD array.")
@click.pass_obj
def jsonld(context: Context, file: Optional[Path], output: Optional[Path]) -> None:
    """Convert parsed frontmatter blocks to canonical JSON-LD."""
    if file:
        data = frontmatter_from_path(file)
        if data is None:
            click.echo(f"No valid frontmatter block found in {file.name}", err=True)
            sys.exit(1)
        jsonld_str = json.dumps(data, indent=2)
        if output:
            output.write_text(jsonld_str, encoding="utf-8")
            click.echo(f"Written JSON-LD to {output}")
        else:
            click.echo(jsonld_str)
        sys.exit(0)

    converted_list = []
    if context.wiki_dir.exists():
        for md_file in sorted(context.wiki_dir.glob("*.md")):
            data = frontmatter_from_path(md_file)
            if data:
                converted_list.append({"file": md_file.name, "jsonld": data})

    output_str = json.dumps(converted_list, indent=2)
    if output:
        output.write_text(output_str, encoding="utf-8")
        click.echo(f"Compiled and written JSON-LD array to {output}")
    else:
        click.echo(output_str)


if __name__ == "__main__":
    main()
