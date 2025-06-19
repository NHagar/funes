"""Command-line interface for MemChat."""

import json
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .orchestrator import chat_run, get_available_models
from .tui import run_tui

app = typer.Typer(
    name="memchat",
    help="Transparent memory-aware chat sandbox for rapid LLM prototyping",
    no_args_is_help=True,
)
console = Console()


@app.command()
def chat(
    prompt: Optional[str] = typer.Option(
        None,
        "--prompt",
        "-p",
        help="Chat prompt to process (if not provided, launches TUI)",
    ),
    model: str = typer.Option(
        "gpt-4o-mini", "--model", "-m", help="OpenAI model to use"
    ),
    memory: Optional[str] = typer.Option(
        None, "--memory", help="Path to memory directory (default: ./memory)"
    ),
    json_output: bool = typer.Option(False, "--json", help="Output results as JSON"),
    diff: bool = typer.Option(
        False, "--diff", help="Show diff between baseline and augmented responses"
    ),
    list_models: bool = typer.Option(
        False, "--list-models", help="List available OpenAI models"
    ),
) -> None:
    """Run MemChat with the specified options."""

    # Handle list models command
    if list_models:
        _list_available_models()
        return

    # Set memory directory
    memory_dir = Path(memory) if memory else Path.cwd() / "memory"

    # If no prompt provided, launch TUI
    if not prompt:
        console.print("[green]Launching MemChat TUI...[/green]")
        console.print(f"[dim]Memory directory: {memory_dir}[/dim]")
        run_tui(memory_dir=str(memory_dir))
        return

    # Run headless mode with prompt
    _run_headless(prompt, model, memory_dir, json_output, diff)


def _list_available_models() -> None:
    """List available OpenAI models."""
    try:
        models = get_available_models()
        console.print("[green]Available OpenAI models:[/green]")
        for model in models:
            console.print(f"  • {model}")
    except Exception as e:
        console.print(f"[red]Error fetching models: {e}[/red]")
        sys.exit(1)


def _run_headless(
    prompt: str, model: str, memory_dir: Path, json_output: bool, show_diff: bool
) -> None:
    """Run MemChat in headless mode."""
    try:
        # Ensure memory directory exists
        memory_dir.mkdir(exist_ok=True)

        console.print("[green]Running MemChat...[/green]")
        console.print(f"[dim]Model: {model}[/dim]")
        console.print(f"[dim]Memory directory: {memory_dir}[/dim]")
        console.print()

        # Run chat
        baseline, augmented, events = chat_run(
            prompt=prompt, model=model, memory_dir=str(memory_dir)
        )

        if json_output:
            _output_json(prompt, baseline, augmented, events, model)
        else:
            _output_formatted(prompt, baseline, augmented, events, show_diff)

    except Exception as e:
        if json_output:
            error_result = {
                "error": str(e),
                "prompt": prompt,
                "model": model,
                "baseline": "",
                "augmented": "",
                "tool_events": [],
            }
            console.print(json.dumps(error_result, indent=2))
        else:
            console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


def _output_json(
    prompt: str, baseline: str, augmented: str, events: list, model: str
) -> None:
    """Output results as JSON."""
    result = {
        "prompt": prompt,
        "model": model,
        "baseline": baseline,
        "augmented": augmented,
        "tool_events": [event.to_dict() for event in events],
    }
    console.print(json.dumps(result, indent=2))


def _output_formatted(
    prompt: str, baseline: str, augmented: str, events: list, show_diff: bool
) -> None:
    """Output results with rich formatting."""

    # Show prompt
    console.print(Panel(prompt, title="[bold]Prompt[/bold]", border_style="blue"))
    console.print()

    # Show baseline response
    console.print(
        Panel(
            baseline,
            title="[bold]Baseline Response (No Memory)[/bold]",
            border_style="green",
        )
    )
    console.print()

    # Show augmented response
    console.print(
        Panel(
            augmented,
            title="[bold]Memory-Augmented Response[/bold]",
            border_style="yellow",
        )
    )
    console.print()

    # Show tool events if any
    if events:
        console.print("[bold]Tool Call Log:[/bold]")
        for i, event in enumerate(events, 1):
            console.print(f"  {i}. [cyan]{event.tool_name}[/cyan] at {event.timestamp}")
            if event.arguments:
                console.print(f"     Args: {event.arguments}")
            result_preview = (
                event.result[:100] + "..." if len(event.result) > 100 else event.result
            )
            console.print(f"     Result: {result_preview}")
        console.print()

    # Show diff if requested
    if show_diff:
        _show_diff(baseline, augmented)


def _show_diff(baseline: str, augmented: str) -> None:
    """Show diff between baseline and augmented responses."""
    import difflib

    baseline_lines = baseline.splitlines(keepends=True)
    augmented_lines = augmented.splitlines(keepends=True)

    diff = list(
        difflib.unified_diff(
            baseline_lines,
            augmented_lines,
            fromfile="baseline",
            tofile="augmented",
            lineterm="",
        )
    )

    if diff:
        console.print("[bold]Diff (baseline → augmented):[/bold]")
        diff_text = "".join(diff)
        syntax = Syntax(diff_text, "diff", theme="monokai", line_numbers=True)
        console.print(syntax)
    else:
        console.print("[dim]No differences between responses.[/dim]")


def main() -> None:
    """Main entry point for the CLI."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
