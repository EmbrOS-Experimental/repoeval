"""RepoEval CLI — run, import, report, compare."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from repoeval.core.models import BenchmarkRun, Task
from repoeval.importers.github import GitHubImporter, GitHistoryImporter, JSONImporter
from repoeval.executors.runner import LocalTaskExecutor, ShellAgentRunner
from repoeval.scorers.patch import CompositeScorer
from repoeval.scorers.leaderboard import LeaderboardGenerator

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="repoeval")
def cli() -> None:
    """RepoEval — Turn your repo history into coding agent benchmarks."""
    pass


@cli.command()
@click.argument("tasks_file", type=click.Path(exists=True))
@click.option("--agent", default="shell", help="Agent type: shell, aider")
@click.option("--model", default="unknown", help="Model name")
@click.option("--command", default="echo 'No agent configured'", help="Shell command template")
@click.option("--output", "-o", default="./benchmark-results", help="Output directory")
@click.option("--max-tasks", default=0, help="Max tasks to run (0=all)")
@click.option("--name", default="", help="Benchmark run name")
def run(
    tasks_file: str,
    agent: str,
    model: str,
    command: str,
    output: str,
    max_tasks: int,
    name: str,
) -> None:
    """Run a benchmark against tasks from a JSON/JSONL file."""
    # Load tasks
    tasks = JSONImporter.from_json(tasks_file)
    if max_tasks > 0:
        tasks = tasks[:max_tasks]

    console.print(f"[bold]Loaded {len(tasks)} tasks[/bold] from {tasks_file}")

    if not tasks:
        console.print("[red]No tasks to run.[/red]")
        sys.exit(1)

    # Create runner
    if agent == "shell":
        runner = ShellAgentRunner(command=command.split())
    else:
        console.print(f"[red]Unknown agent: {agent}[/red]")
        sys.exit(1)

    # Create benchmark run
    bench = BenchmarkRun(
        name=name or f"Benchmark {tasks_file}",
        agent_type=agent,
        model=model,
        tasks=tasks,
    )

    # Execute
    executor = LocalTaskExecutor(runner)
    scorer = CompositeScorer()

    console.print(f"\n[bold]Running {len(tasks)} tasks with {agent}...[/bold]\n")
    
    results = executor.execute_all(
        tasks,
        callback=lambda task, result: console.print(
            f"  {'✓' if result.status.value == 'passed' else '✗'} "
            f"{task.issue_title[:60]} — {result.status.value}"
        ),
    )

    bench.results = results
    bench.passed = sum(1 for r in results if r.status.value == "passed")
    bench.failed = sum(1 for r in results if r.status.value == "failed")
    bench.total_tasks = len(results)
    bench.finalize()

    # Show summary
    console.print(Panel(
        f"[bold]Pass Rate:[/bold] [green]{bench.passed}[/green]/{bench.total_tasks} "
        f"({bench.pass_rate:.0%})\n"
        f"[bold]Total Duration:[/bold] {bench.total_duration_ms / 1000:.0f}s\n"
        f"[bold]Total Cost:[/bold] ${bench.total_cost_usd:.4f}\n"
        f"[bold]Tokens:[/bold] {bench.total_tokens:,}",
        title=f"Benchmark Complete: {bench.name}",
        border_style="orange",
    ))

    # Generate leaderboard
    gen = LeaderboardGenerator()
    html_path = gen.generate(bench, output_dir=output)
    console.print(f"\n[green]Leaderboard saved to:[/green] {html_path}")

    # Save JSON
    json_path = Path(output) / "results.json"
    console.print(f"[green]Results saved to:[/green] {json_path}")


@cli.command()
@click.argument("repo_path", type=click.Path(exists=True), default=".")
@click.option("--output", "-o", required=True, help="Output JSON file for tasks")
@click.option("--max-commits", default=20, help="Max bug-fix commits to import")
@click.option("--min-commit", default="", help="Minimum commit hash to consider")
def import_git(
    repo_path: str,
    output: str,
    max_commits: int,
    min_commit: str,
) -> None:
    """Import tasks from git history — find bug-fix commits."""
    importer = GitHistoryImporter(repo_path)
    
    console.print(f"Scanning {repo_path} for bug-fix commits...")
    tasks = importer.create_tasks_from_commits(max_count=max_commits)

    if not tasks:
        console.print("[yellow]No bug-fix commits found.[/yellow]")
        sys.exit(1)

    # Save tasks as JSON
    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([t.model_dump(mode="json") for t in tasks], f, indent=2, default=str)

    console.print(f"[green]Imported {len(tasks)} tasks[/green] → {output_path}")

    # Show summary
    table = Table(title="Imported Tasks")
    table.add_column("ID", style="dim")
    table.add_column("Issue")
    table.add_column("Commit", style="cyan")
    for task in tasks[:10]:
        meta = task.metadata
        table.add_row(
            task.id,
            task.issue_title[:50],
            meta.get("fix_commit", "")[:8],
        )
    console.print(table)
    if len(tasks) > 10:
        console.print(f"[dim]... and {len(tasks) - 10} more[/dim]")


@cli.command()
@click.argument("owner")
@click.argument("repo")
@click.option("--output", "-o", required=True, help="Output JSON file")
@click.option("--labels", default="bug", help="Comma-separated labels to filter")
@click.option("--max-issues", default=50, help="Max issues to import")
@click.option("--state", default="closed", help="Issue state: open, closed, all")
@click.option("--token", envvar="GITHUB_TOKEN", default=None, help="GitHub API token")
def import_github(
    owner: str,
    repo: str,
    output: str,
    labels: str,
    max_issues: int,
    state: str,
    token: Optional[str],
) -> None:
    """Import tasks from GitHub issues."""
    importer = GitHubImporter(token=token)
    
    console.print(f"Fetching issues from {owner}/{repo}...")
    tasks = importer.fetch_issues(
        owner, repo,
        state=state,
        labels=labels,
        max_count=max_issues,
    )

    if not tasks:
        console.print("[yellow]No issues found.[/yellow]")
        sys.exit(1)

    output_path = Path(output)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump([t.model_dump(mode="json") for t in tasks], f, indent=2, default=str)

    console.print(f"[green]Imported {len(tasks)} tasks[/green] → {output_path}")

    table = Table(title="Imported Issues")
    table.add_column("#", style="dim")
    table.add_column("Title")
    for task in tasks[:10]:
        table.add_row(task.instance_id, task.issue_title[:60])
    console.print(table)


@cli.command()
@click.argument("results_file", type=click.Path(exists=True))
@click.option("--output", "-o", default="./leaderboard", help="Output directory")
@click.option("--title", default="Benchmark Results", help="Leaderboard title")
def report(results_file: str, output: str, title: str) -> None:
    """Generate leaderboard from results JSON."""
    data = json.loads(Path(results_file).read_text())
    run = BenchmarkRun.model_validate(data)

    gen = LeaderboardGenerator()
    html_path = gen.generate(run, output_dir=output, title=title)
    
    console.print(f"[green]Leaderboard:[/green] {html_path}")
    console.print(f"\nPass Rate: [bold]{run.pass_rate:.0%}[/bold]")
    console.print(f"Passed: [green]{run.passed}[/red]/{run.total_tasks}")


@cli.command()
@click.argument("results_files", nargs=-1, required=True)
@click.option("--output", "-o", default="./comparison", help="Output directory")
@click.option("--title", default="Model Comparison", help="Comparison title")
def compare(results_files: list[str], output: str, title: str) -> None:
    """Compare multiple benchmark result files."""
    runs = []
    for f in results_files:
        data = json.loads(Path(f).read_text())
        runs.append(BenchmarkRun.model_validate(data))

    if len(runs) < 2:
        console.print("[red]Need at least 2 result files to compare.[/red]")
        sys.exit(1)

    # Show comparison table
    table = Table(title=title)
    table.add_column("Run", style="bold")
    table.add_column("Agent", style="cyan")
    table.add_column("Pass Rate", style="bold")
    table.add_column("Passed")
    table.add_column("Duration")
    table.add_column("Cost")

    for run in runs:
        color = "green" if run.pass_rate >= 0.5 else "red"
        table.add_row(
            run.name or run.id[:8],
            run.agent_type,
            f"[{color}]{run.pass_rate:.0%}[/{color}]",
            f"{run.passed}/{run.total_tasks}",
            f"{run.total_duration_ms / 1000:.0f}s",
            f"${run.total_cost_usd:.2f}",
        )

    console.print(table)

    # Generate comparison HTML
    gen = LeaderboardGenerator()
    html_path = gen.generate_comparison(runs, output_dir=output, title=title)
    console.print(f"\n[green]Comparison saved:[/green] {html_path}")


@cli.command()
@click.argument("tasks_file", type=click.Path(exists=True))
def validate(tasks_file: str) -> None:
    """Validate a tasks JSON file."""
    try:
        tasks = JSONImporter.from_json(tasks_file)
        console.print(f"[green]✓ Valid — {len(tasks)} tasks[/green]")
        
        for i, task in enumerate(tasks[:5]):
            console.print(f"  {i+1}. [{task.id}] {task.issue_title[:60]}")
        if len(tasks) > 5:
            console.print(f"  ... and {len(tasks) - 5} more")
    except Exception as e:
        console.print(f"[red]✗ Invalid: {e}[/red]")
        sys.exit(1)


def main() -> None:
    cli()
