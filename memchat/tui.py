"""Textual TUI for MemChat application."""

from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Container
from textual.reactive import reactive
from textual.widgets import (
    Button,
    DataTable,
    Footer,
    Header,
    Input,
    MarkdownViewer,
    Select,
    Static,
)
from textual.worker import Worker

from .orchestrator import ToolCallEvent, chat_run, get_available_models
from .tools import MEM_DIR


class MemChatApp(App):
    """Main MemChat TUI application."""

    CSS = """
    .main-container {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        height: 100%;
    }

    .model-selector {
        column-span: 2;
        height: 3;
    }

    /* The two panes follow insertion order: row 2 col 1 then row 2 col 2 */
    .baseline-pane {
        border: solid $primary;
    }

    .augmented-pane {
        border: solid $secondary;
    }

    .tool-log {
        height: 10;
        border: solid $accent;
    }

    .input-area {
        height: 5;
        border: solid $success;
    }

    .status-bar {
        height: 1;
        background: $surface;
    }

    #prompt-input {
        height: 3;
    }

    #tool-table {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
        ("ctrl+r", "clear_responses", "Clear Responses"),
        ("enter", "submit_prompt", "Submit Prompt"),
    ]

    current_model = reactive("gpt-4o-mini")
    is_processing = reactive(False)

    def __init__(self, memory_dir: Optional[str] = None):
        super().__init__()
        self.memory_dir = memory_dir
        self.available_models: list[str] = []

    async def on_mount(self) -> None:
        """Initialize the app on mount."""
        # Load available models
        self.run_worker(self._load_models, exclusive=True)

        # Set up initial memory directory
        if self.memory_dir:
            from pathlib import Path

            from . import tools

            tools.MEM_DIR = Path(self.memory_dir)

        MEM_DIR.mkdir(exist_ok=True)

    def on_ready(self) -> None:
        self.query_one("#status", Static).update(f"Memory directory: {MEM_DIR}")

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()

        # --------- MAIN GRID -------------------------------------------------
        with Container(classes="main-container"):
            # ▸ 1. Model selector row
            with Container(classes="model-selector"):
                yield Static("Model:", id="model-label")
                yield Select([("Loading…", "loading")], id="model-select")
                yield Button("Refresh Models", id="refresh-models", variant="default")

            # ▸ 2. Baseline pane (row 2, col 1)
            baseline = MarkdownViewer(
                "Select a model and enter a prompt to see the baseline response.",
                classes="baseline-pane",
                id="baseline-viewer",
            )
            baseline.border_title = "Baseline (No Memory)"
            yield baseline

            # ▸ 3. Augmented pane (row 2, col 2)
            augmented = MarkdownViewer(
                "The memory-augmented response will appear here.",
                classes="augmented-pane",
                id="augmented-viewer",
            )
            augmented.border_title = "With Memory"
            yield augmented

        # --------- TOOL CALL LOG --------------------------------------------
        tool_log = Container(classes="tool-log")
        tool_log.border_title = "Tool Call Log"
        yield tool_log

        with tool_log:
            yield DataTable(id="tool-table")

        # --------- PROMPT INPUT AREA ----------------------------------------
        prompt_input = Container(classes="input-area")
        prompt_input.border_title = "Prompt Input"
        yield prompt_input

        with prompt_input:
            yield Input(placeholder="Enter your prompt here…", id="prompt-input")
            with Container():  # small horizontal stack
                yield Button("Submit", id="submit-btn", variant="primary")
                yield Button("Clear", id="clear-btn", variant="default")

        # --------- STATUS BAR + FOOTER --------------------------------------
        yield Static("Ready", id="status", classes="status-bar")  # ← restores #status
        yield Footer()

    async def _load_models(self) -> list[str]:
        """Load available OpenAI models."""
        return get_available_models()

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle worker state changes."""
        if event.worker.name == "_load_models":
            if event.state == "success":
                models = event.worker.result
                self.available_models = models
                model_select = self.query_one("#model-select", Select)

                # Update model options
                model_select.set_options([(m, m) for m in models])

                # Set default model
                default = "gpt-4o-mini"
                model_select.value = default
                self.current_model = default

        elif event.worker.name == "_run_chat":
            baseline_viewer = self.query_one("#baseline-viewer", MarkdownViewer)
            augmented_viewer = self.query_one("#augmented-viewer", MarkdownViewer)
            status = self.query_one("#status", Static)

            if event.state == "success":
                baseline, augmented, events = event.worker.result
                baseline_viewer.update(baseline)  # <-- update, not .document
                augmented_viewer.update(augmented)
                self._update_tool_table(events)

                tool_count = len(events)
                plural = "s" if tool_count != 1 else ""
                status.update(f"Complete. {tool_count} tool call{plural} made.")
            elif event.state == "error":
                error_msg = f"Error: {event.worker.error}"
                baseline_viewer.update(error_msg)
                augmented_viewer.update(error_msg)
                status.update("Error occurred during processing")

            self.is_processing = False

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle model selection change."""
        if event.select.id == "model-select":
            self.current_model = str(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        match event.button.id:
            case "submit-btn":
                self.action_submit_prompt()
            case "clear-btn":
                self.action_clear_responses()
            case "refresh-models":
                self.run_worker(self._load_models, exclusive=True)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if event.input.id == "prompt-input":
            self.action_submit_prompt()

    def action_submit_prompt(self) -> None:
        """Submit the current prompt for processing."""
        prompt_input = self.query_one("#prompt-input", Input)
        prompt = prompt_input.value.strip()

        if not prompt:
            self.query_one("#status", Static).update("Please enter a prompt")
            return
        if self.is_processing:
            self.query_one("#status", Static).update("Already processing a request…")
            return

        # Clear input and start processing
        prompt_input.value = ""
        self.is_processing = True
        self.query_one("#status", Static).update("Processing…")

        self.run_worker(self._run_chat, prompt, self.current_model, exclusive=True)

    async def _run_chat(self, prompt: str, model: str):
        """Run chat session in background worker."""
        try:
            return chat_run(prompt=prompt, model=model, memory_dir=self.memory_dir)
        except Exception as e:
            return (f"Error: {e}",) * 3  # baseline, augmented, events

    def _update_tool_table(self, events: list[ToolCallEvent]) -> None:
        """Update the tool call table with events."""
        table = self.query_one("#tool-table", DataTable)
        table.clear(columns=True)

        if not events:
            return

        table.add_columns("Time", "Tool", "Arguments", "Result")
        for ev in events:
            table.add_row(
                ev.timestamp.split("T")[1][:8],
                ev.tool_name,
                str(ev.arguments),
                (ev.result[:50] + "…") if len(ev.result) > 50 else ev.result,
            )

    def action_clear_responses(self) -> None:
        """Clear all response panes and tool table."""
        self.query_one("#baseline-viewer", MarkdownViewer).update(
            "Select a model and enter a prompt to see the baseline response."
        )
        self.query_one("#augmented-viewer", MarkdownViewer).update(
            "The memory-augmented response will appear here."
        )
        self.query_one("#tool-table", DataTable).clear(columns=True)
        self.query_one("#status", Static).update("Cleared")


def run_tui(memory_dir: Optional[str] = None) -> None:
    """Run the MemChat TUI application."""
    MemChatApp(memory_dir=memory_dir).run()
