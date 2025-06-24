import asyncio
from pathlib import Path

from agents import Agent, Runner, ToolCallItem, function_tool
from openai import OpenAI

MEM_DIR = Path.cwd() / "memory"


def base_response(prompt: str, model: str = "gpt-4.1") -> str:
    """Get a baseline response from the model without memory tools."""
    client = OpenAI()
    response = client.responses.create(model=model, input=prompt)
    return response.output_text


# function tools
@function_tool
def list_memory_files() -> list[str]:
    """List all memory files recursively from the memory directory.

    Returns:
        List of relative file paths from the memory directory.
    """
    if not MEM_DIR.exists():
        MEM_DIR.mkdir(exist_ok=True)
        return []

    files = MEM_DIR.glob("**/*")
    files = [
        str(file.relative_to(MEM_DIR))
        for file in files
        if file.is_file() and not file.name.startswith(".")
    ]
    files.sort()
    return files


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


async def main(prompt, model):
    """Run the agent asynchronously."""
    agent = Agent(
        name="funes",
        instructions="""You are a helpful assistant that can access additional information stored in memory files. 
        You should ALWAYS call the list_memory_files tool to see if any are relevant to the user's query. 
        If you find relevant files, use the read_memory_file tool to read their contents.""",
        tools=[list_memory_files, read_memory_file],
        model=model,
    )

    runner = Runner()
    response = await runner.run(
        agent,
        input=prompt,
    )

    output_text = response.final_output
    new_items = response.new_items
    tool_calls = [i.raw_item.name for i in new_items if isinstance(i, ToolCallItem)]  # type: ignore
    print([i.raw_item.arguments for i in new_items if isinstance(i, ToolCallItem)])  # type: ignore

    print("Agent Response:", output_text)
    print("Tool Calls:", tool_calls)


if __name__ == "__main__":
    MODEL = "gpt-4.1"
    PROMPT = "What is a good library for data visualization?"

    base = base_response(PROMPT, model=MODEL)
    print("Baseline Response:", base)
    print("========================")

    asyncio.run(main(PROMPT, MODEL))
