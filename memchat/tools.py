"""Memory file tools for the OpenAI agent."""

import os
from pathlib import Path

MEM_DIR = Path.cwd() / "memory"


def list_memory_files() -> list[str]:
    """List all memory files recursively from the memory directory.

    Returns:
        List of relative file paths from the memory directory.
    """
    if not MEM_DIR.exists():
        MEM_DIR.mkdir(exist_ok=True)
        return []

    files = []
    for root, _, filenames in os.walk(MEM_DIR):
        for filename in filenames:
            if filename.startswith("."):
                continue
            full_path = Path(root) / filename
            relative_path = full_path.relative_to(MEM_DIR)
            files.append(str(relative_path))

    return sorted(files)


def read_memory_file(path: str) -> str:
    """Read a memory file by its relative path.

    Args:
        path: Relative path from the memory directory

    Returns:
        File contents as UTF-8 string

    Raises:
        FileNotFoundError: If the file doesn't exist
        UnicodeDecodeError: If the file isn't valid UTF-8
    """
    file_path = MEM_DIR / path

    # Security check: ensure the path is within memory directory
    try:
        file_path.resolve().relative_to(MEM_DIR.resolve())
    except ValueError as e:
        raise ValueError(f"Path outside memory directory: {path}") from e

    if not file_path.exists():
        raise FileNotFoundError(f"Memory file not found: {path}")

    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    try:
        return file_path.read_text(encoding="utf-8")
    except UnicodeDecodeError as e:
        raise UnicodeDecodeError(
            e.encoding,
            e.object,
            e.start,
            e.end,
            f"File {path} is not valid UTF-8: {e.reason}",
        ) from e


# Tool definitions for OpenAI function calling
MEMORY_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "list_memory_files",
            "description": "List all available memory files that can be read",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_memory_file",
            "description": "Read the contents of a specific memory file",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the memory file to read",
                    }
                },
                "required": ["path"],
            },
        },
    },
]


def execute_tool_call(tool_name: str, arguments: dict) -> str:
    """Execute a tool call and return the result as a string.

    Args:
        tool_name: Name of the tool to execute
        arguments: Dictionary of arguments for the tool

    Returns:
        String result of the tool execution
    """
    if tool_name == "list_memory_files":
        files = list_memory_files()
        if not files:
            return "No memory files found."
        return "\n".join(f"- {file}" for file in files)

    elif tool_name == "read_memory_file":
        path = arguments.get("path")
        if not path:
            return "Error: 'path' parameter is required"

        try:
            content = read_memory_file(path)
            return f"Contents of {path}:\n\n{content}"
        except (FileNotFoundError, ValueError, UnicodeDecodeError) as e:
            return f"Error reading {path}: {str(e)}"

    else:
        return f"Error: Unknown tool '{tool_name}'"
