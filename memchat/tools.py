"""Memory file tools for the OpenAI agent."""

import os
from pathlib import Path

from agents import function_tool

MEM_DIR = Path.cwd() / "memory"


@function_tool
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


@function_tool
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
