"""CLI for skillregistry."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

import typer

from skillregistry.eval import load_eval_dataset, run_ablation, run_eval
from skillregistry.registry import SkillRegistry

app = typer.Typer(
    name="skillregistry",
    help="Semantic skill registry — register, search, and evaluate skills.",
    no_args_is_help=True,
)


@app.command()
def register(
    paths: list[str] = typer.Argument(..., help="Directories to scan for SKILL.md"),
    output: Path = typer.Option(
        Path(".skill-index"), "--output", "-o", help="Output index directory"
    ),
    llm: str = typer.Option("mock", "--llm", help="LLM backend (mock, openai:gpt-4o-mini)"),
    embedder: str = typer.Option("mock", "--embedder", help="Embedder (mock, local)"),
    index_mode: str = typer.Option("full", "--index-mode", help="description or full"),
    no_auto_metadata: bool = typer.Option(
        False, "--no-auto-metadata", help="Skip LLM metadata generation"
    ),
    changed_only: bool = typer.Option(
        False, "--changed-only", help="Only regenerate changed skills"
    ),
) -> None:
    """Scan skills, generate metadata, and build search index."""
    registry = SkillRegistry.from_paths(
        paths,
        llm=llm,
        auto_metadata=not no_auto_metadata,
        embedder=embedder,
        index_mode=index_mode,  # type: ignore[arg-type]
    )

    if changed_only and output.exists():
        registry = SkillRegistry.from_directory(output)
        registry.paths = [str(p) for p in paths]
        registry.llm = llm
        registry.auto_metadata = not no_auto_metadata

    count = registry.register(changed_only=changed_only)
    registry.save(output)
    typer.echo(f"Registered {len(registry)} skills ({count} new/updated) -> {output}")


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    index_dir: Path = typer.Option(
        Path(".skill-index"), "--index", "-i", help="Index directory"
    ),
    top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
) -> None:
    """Search the skill registry."""
    registry = SkillRegistry.from_directory(index_dir)
    matches = registry.retrieve(query, top_k=top_k)

    if not matches:
        typer.echo("No matches found.")
        raise typer.Exit(0)

    for i, m in enumerate(matches, 1):
        typer.echo(f"{i}. [{m.score:.3f}] {m.name} — {m.description[:80]}")


@app.command("list")
def list_skills(
    index_dir: Path = typer.Option(
        Path(".skill-index"), "--index", "-i", help="Index directory"
    ),
) -> None:
    """List all registered skills."""
    registry = SkillRegistry.from_directory(index_dir)
    for r in registry.records:
        src = r.metadata_source
        n_q = len(r.trigger_questions)
        typer.echo(f"- {r.name} ({r.id}) [{src}, {n_q} questions]")


@app.command()
def show(
    skill_id: str = typer.Argument(..., help="Skill id or name"),
    index_dir: Path = typer.Option(
        Path(".skill-index"), "--index", "-i", help="Index directory"
    ),
    body: bool = typer.Option(False, "--body", help="Include full SKILL.md body"),
) -> None:
    """Show skill metadata."""
    registry = SkillRegistry.from_directory(index_dir)
    record = registry.get_record(skill_id)

    typer.echo(f"Name: {record.name}")
    typer.echo(f"ID: {record.id}")
    typer.echo(f"Path: {record.path}")
    typer.echo(f"Description: {record.description}")
    typer.echo(f"Metadata source: {record.metadata_source}")
    if record.one_line_summary:
        typer.echo(f"Summary: {record.one_line_summary}")
    if record.tags:
        typer.echo(f"Tags: {', '.join(record.tags)}")
    if record.trigger_questions:
        typer.echo("Trigger questions:")
        for q in record.trigger_questions:
            typer.echo(f"  - {q}")

    if body:
        doc = registry.load_skill(skill_id)
        typer.echo("\n--- Body ---\n")
        typer.echo(doc.body)


@app.command("eval")
def eval_cmd(
    index_dir: Optional[Path] = typer.Option(
        None, "--index", "-i", help="Existing index (skip if using --paths)"
    ),
    paths: Optional[list[str]] = typer.Option(
        None, "--paths", help="Skill dirs to register before eval"
    ),
    dataset: Path = typer.Option(
        Path("eval/queries.jsonl"), "--dataset", "-d", help="Eval queries JSONL"
    ),
    top_k: list[int] = typer.Option([1, 3, 5], "--top-k", "-k", help="Recall@k values"),
    index_mode: str = typer.Option("full", "--index-mode", help="description or full"),
    embedder: str = typer.Option("mock", "--embedder"),
    llm: str = typer.Option("mock", "--llm"),
    ablate: bool = typer.Option(
        False, "--ablate", help="Run description vs full ablation"
    ),
    report: Optional[Path] = typer.Option(
        None, "--report", "-r", help="Write markdown report to file"
    ),
) -> None:
    """Evaluate retrieval quality (Recall@k, MRR)."""
    eval_queries = load_eval_dataset(dataset)

    if ablate:
        if not paths:
            typer.echo("--ablate requires --paths")
            raise typer.Exit(1)
        results = run_ablation(paths, str(dataset), embedder=embedder, llm=llm, top_k_values=top_k)
        lines = ["# Ablation Results\n"]
        for mode, result in results.items():
            lines.append(result.format_report())
            lines.append("")
        output = "\n".join(lines)
        typer.echo(output)
        if report:
            report.write_text(output, encoding="utf-8")
        return

    if paths:
        registry = SkillRegistry.from_paths(
            paths, llm=llm, embedder=embedder, index_mode=index_mode  # type: ignore
        )
        registry.register()
    elif index_dir:
        registry = SkillRegistry.from_directory(index_dir)
    else:
        typer.echo("Provide --index or --paths")
        raise typer.Exit(1)

    result = run_eval(registry, eval_queries, top_k_values=top_k, index_mode=index_mode)  # type: ignore
    output = result.format_report()
    typer.echo(output)
    if report:
        report.write_text(output, encoding="utf-8")


if __name__ == "__main__":
    app()
