"""Orchestrator for running baseline and memory-augmented chat sessions."""

import json
from datetime import datetime
from typing import Any, Optional

from openai import OpenAI

from .tools import MEMORY_TOOLS, execute_tool_call


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
    augmented_response, tool_events = _run_augmented_chat(client, prompt, model)

    return baseline_response, augmented_response, tool_events


def _run_baseline_chat(client: OpenAI, prompt: str, model: str) -> str:
    """Run baseline chat completion without any tools."""
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=1000,
        )

        return response.choices[0].message.content or ""

    except Exception as e:
        return f"Error in baseline chat: {str(e)}"


def _run_augmented_chat(
    client: OpenAI, prompt: str, model: str
) -> tuple[str, list[ToolCallEvent]]:
    """Run chat completion with memory tools available."""
    tool_events = []
    messages = [{"role": "user", "content": prompt}]

    try:
        # Initial chat completion with tools
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=MEMORY_TOOLS,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=1000,
        )

        response_message = response.choices[0].message
        messages.append(
            {
                "role": "assistant",
                "content": response_message.content,
                "tool_calls": response_message.tool_calls,
            }
        )

        # Handle tool calls if any
        if response_message.tool_calls:
            for tool_call in response_message.tool_calls:
                timestamp = datetime.now().isoformat()

                # Execute the tool call
                try:
                    arguments = json.loads(tool_call.function.arguments)
                    result = execute_tool_call(tool_call.function.name, arguments)

                    # Log the tool call event
                    event = ToolCallEvent(
                        timestamp=timestamp,
                        tool_name=tool_call.function.name,
                        arguments=arguments,
                        result=result,
                    )
                    tool_events.append(event)

                    # Add tool result to messages
                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        }
                    )

                except Exception as e:
                    error_result = (
                        f"Error executing {tool_call.function.name}: {str(e)}"
                    )
                    event = ToolCallEvent(
                        timestamp=timestamp,
                        tool_name=tool_call.function.name,
                        arguments={},
                        result=error_result,
                    )
                    tool_events.append(event)

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": error_result,
                        }
                    )

            # Get final response after tool calls
            final_response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=MEMORY_TOOLS,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=1000,
            )

            final_message = final_response.choices[0].message
            return final_message.content or "", tool_events

        else:
            # No tool calls, return the original response
            return response_message.content or "", tool_events

    except Exception as e:
        error_msg = f"Error in augmented chat: {str(e)}"
        return error_msg, tool_events


def get_available_models() -> list[str]:
    """Get list of available OpenAI models.

    Returns:
        List of model names, with fallback to common models if API fails.
    """
    return ["gpt-4o", "gpt-4o-mini", "o3", "o4-mini", "gpt-4.1", "gpt-4.1-mini"]
