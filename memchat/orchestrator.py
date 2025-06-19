"""Orchestrator for running baseline and memory-augmented chat sessions."""

from datetime import datetime
from typing import Any, Optional

from agents import Agent, Runner, ToolCallItem
from openai import OpenAI

from .tools import list_memory_files, read_memory_file


class ToolCallEvent:
    """Represents a tool call event for logging."""

    def __init__(
        self, timestamp: str, tool_name: str, arguments: dict[str, Any], result: str
    ):
        self.timestamp = timestamp
        self.tool_name = tool_name
        self.arguments = arguments
        self.result = result

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "result": self.result,
        }


def chat_run(
    prompt: str, model: str = "gpt-4o-mini", memory_dir: Optional[str] = None
) -> tuple[str, str, list[ToolCallEvent]]:
    """Run a chat session with both baseline and memory-augmented responses.

    Args:
        prompt: User's chat prompt
        model: OpenAI model to use (default: gpt-4o-mini)
        memory_dir: Optional custom memory directory path

    Returns:
        Tuple of (baseline_response, augmented_response, tool_events)
    """
    client = OpenAI()

    # Update memory directory if custom path provided
    if memory_dir:
        from pathlib import Path

        from . import tools

        tools.MEM_DIR = Path(memory_dir)

    # Run baseline chat (no tools)
    baseline_response = _run_baseline_chat(client, prompt, model)

    # Run augmented chat (with memory tools)
    augmented_response, tool_events = _run_augmented_chat(prompt, model)

    return baseline_response, augmented_response, tool_events


def _run_baseline_chat(client: OpenAI, prompt: str, model: str) -> str:
    """Run baseline chat completion without any tools."""
    try:
        response = client.responses.create(
            model=model,
            input=prompt,
        )
        return response.output_text

    except Exception as e:
        return f"Error in baseline chat: {str(e)}"


def _run_augmented_chat(prompt: str, model: str) -> tuple[str, list[ToolCallEvent]]:
    """Run chat completion with memory tools available."""
    agent = Agent(
        name="MemoryRetriever",
        instructions="Consult memory files when they are relevant to the conversation.",
        tools=[list_memory_files, read_memory_file],
        model=model,
    )

    runner = Runner()
    response = runner.run(
        agent,
        input=prompt,
    )

    try:
        output_text = response.final_output
        new_items = response.new_items
        tool_events = [i for i in new_items if isinstance(i, ToolCallItem)]

        tool_events = [
            ToolCallEvent(
                timestamp=datetime.now().isoformat(),
                tool_name=item.tool_name,
                arguments=item.arguments,
                result=item.result,
            )
            for item in tool_events
        ]

        return output_text, tool_events

    except Exception as e:
        error_msg = f"Error in augmented chat: {str(e)}"
        return error_msg, []


def get_available_models() -> list[str]:
    """Get list of available OpenAI models.

    Returns:
        List of model names, with fallback to common models if API fails.
    """
    return ["gpt-4o", "gpt-4o-mini", "o3", "o4-mini", "gpt-4.1", "gpt-4.1-mini"]
