"""Textual TUI for MemChat application."""

from typing import List, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
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


class MemChatApp(App):
    """Main MemChat TUI application."""

    CSS = """
    .main-container {
        layout: grid;
        grid-size: 2 2;
        grid-gutter: 1;
        height: 1fr;
    }
    
    .model-selector {
        grid-column: 1 / 3;
        height: 3;
    }
    
    .baseline-pane {
        border: solid $primary;
        border-title: "Baseline (No Memory)";
        grid-column: 1;
        grid-row: 2;
    }
    
    .augmented-pane {
        border: solid $secondary;
        border-title: "With Memory";
        grid-column: 2;
        grid-row: 2;
    }
    
    .tool-log {
        height: 10;
        border: solid $accent;
        border-title: "Tool Call Log";
    }
    
    .input-area {
        height: 5;
        border: solid $success;
        border-title: "Prompt Input";
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
        self.available_models: List[str] = []

    async def on_mount(self) -> None:
        """Initialize the app on mount."""
        # Load available models
        worker = self.run_worker(self._load_models, exclusive=True)

        # Set up initial memory directory
        if self.memory_dir:
            from pathlib import Path

            from . import tools

            tools.MEM_DIR = Path(self.memory_dir)

        # Ensure memory directory exists
        from .tools import MEM_DIR

        MEM_DIR.mkdir(exist_ok=True)

        # Update status
        self.query_one("#status", Static).update(f"Memory directory: {MEM_DIR}")

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header()

        with Container(classes="main-container"):
            # Model selector row
            with Horizontal(classes="model-selector"):
                yield Static("Model:", id="model-label")
                yield Select(
                    [("Loading models...", "loading")],
                    value="loading",
                    id="model-select",
                )
                yield Button("Refresh Models", id="refresh-models", variant="outline")

            # Main content panes
            yield MarkdownViewer(
                "Select a model and enter a prompt to see the baseline response.",
                classes="baseline-pane",
                id="baseline-viewer",
            )

            yield MarkdownViewer(
                "The memory-augmented response will appear here.",
                classes="augmented-pane",
                id="augmented-viewer",
            )

        # Tool call log
        with Container(classes="tool-log"):
            yield DataTable(id="tool-table")

        # Input area
        with Container(classes="input-area"):
            yield Input(placeholder="Enter your prompt here...", id="prompt-input")
            with Horizontal():
                yield Button("Submit", id="submit-btn", variant="primary")
                yield Button("Clear", id="clear-btn", variant="outline")

        # Status bar
        yield Static("Ready", id="status", classes="status-bar")
        yield Footer()

    async def _load_models(self) -> List[str]:
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
                options = [(model, model) for model in models]
                model_select.set_options(options)

                # Set default model if available
                if "gpt-4o-mini" in models:
                    model_select.value = "gpt-4o-mini"
                    self.current_model = "gpt-4o-mini"
                elif models:
                    model_select.value = models[0]
                    self.current_model = models[0]

    def on_select_changed(self, event: Select.Changed) -> None:
        """Handle model selection change."""
        if event.select.id == "model-select":
            self.current_model = str(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "submit-btn":
            self.action_submit_prompt()
        elif event.button.id == "clear-btn":
            self.action_clear_responses()
        elif event.button.id == "refresh-models":
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
            self.query_one("#status", Static).update("Already processing a request...")
            return

        # Clear input and start processing
        prompt_input.value = ""
        self.is_processing = True
        self.query_one("#status", Static).update("Processing...")

        # Run chat in background
        self.run_worker(self._run_chat, prompt, self.current_model, exclusive=True)

    async def _run_chat(self, prompt: str, model: str) -> tuple:
        """Run chat session in background worker."""
        try:
            baseline, augmented, events = chat_run(
                prompt=prompt, model=model, memory_dir=self.memory_dir
            )
            return baseline, augmented, events
        except Exception as e:
            return f"Error: {str(e)}", f"Error: {str(e)}", []

    def on_worker_state_changed(self, event: Worker.StateChanged) -> None:
        """Handle chat worker completion."""
        if event.worker.name == "_run_chat":
            if event.state == "success":
                baseline, augmented, events = event.worker.result

                # Update response panes
                self.query_one("#baseline-viewer", MarkdownViewer).document = baseline
                self.query_one("#augmented-viewer", MarkdownViewer).document = augmented

                # Update tool call table
                self._update_tool_table(events)

                # Update status
                tool_count = len(events)
                self.query_one("#status", Static).update(
                    f"Complete. {tool_count} tool call{'s' if tool_count != 1 else ''} made."
                )

            elif event.state == "error":
                error_msg = f"Error: {str(event.worker.error)}"
                self.query_one("#baseline-viewer", MarkdownViewer).document = error_msg
                self.query_one("#augmented-viewer", MarkdownViewer).document = error_msg
                self.query_one("#status", Static).update(
                    "Error occurred during processing"
                )

            self.is_processing = False

    def _update_tool_table(self, events: List[ToolCallEvent]) -> None:
        """Update the tool call table with events."""
        table = self.query_one("#tool-table", DataTable)

        # Clear existing data
        table.clear(columns=True)

        if not events:
            return

        # Add columns
        table.add_columns("Time", "Tool", "Arguments", "Result")

        # Add rows
        for event in events:
            table.add_row(
                event.timestamp.split("T")[1][:8],  # Just time portion
                event.tool_name,
                str(event.arguments),
                event.result[:50] + "..." if len(event.result) > 50 else event.result,
            )

    def action_clear_responses(self) -> None:
        """Clear all response panes and tool table."""
        self.query_one(
            "#baseline-viewer", MarkdownViewer
        ).document = "Select a model and enter a prompt to see the baseline response."
        self.query_one(
            "#augmented-viewer", MarkdownViewer
        ).document = "The memory-augmented response will appear here."

        table = self.query_one("#tool-table", DataTable)
        table.clear(columns=True)

        self.query_one("#status", Static).update("Cleared")

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_tui(memory_dir: Optional[str] = None) -> None:
    """Run the MemChat TUI application."""
    app = MemChatApp(memory_dir=memory_dir)
    app.run()
