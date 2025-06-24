import asyncio
import os
from pathlib import Path

import streamlit as st
from agents import Agent, Runner, ToolCallItem
from openai import OpenAI

from funes.agent import list_memory_files, read_memory_file

MEM_DIR = Path.cwd() / "memory"

OPENAI_MODELS = ["gpt-4o", "gpt-4o-mini", "gpt-4.1", "gpt-4.1-mini", "o3", "o4-mini"]


def get_base_response(prompt: str, model: str, api_key: str) -> str:
    """Get a baseline response from the model without memory tools."""
    client = OpenAI(api_key=api_key)
    response = client.responses.create(model=model, input=prompt)
    return response.output_text


async def get_agent_response(
    prompt: str, model: str, api_key: str
) -> tuple[str, list[dict]]:
    """Get response from agent with memory tools."""
    # Set API key in environment for the agents library
    os.environ["OPENAI_API_KEY"] = api_key

    agent = Agent(
        name="funes",
        instructions="""You are a helpful assistant that can access additional information stored in memory files. 
        You should ALWAYS call the list_memory_files tool to see if any are relevant to the user's query. 
        If you find relevant files, use the read_memory_file tool to read their contents.""",
        tools=[list_memory_files, read_memory_file],
        model=model,
    )

    runner = Runner()
    response = await runner.run(agent, input=prompt)

    output_text = response.final_output
    new_items = response.new_items
    tool_calls = [
        {"name": i.raw_item.name, "arguments": i.raw_item.arguments}
        for i in new_items
        if isinstance(i, ToolCallItem)
    ]

    return output_text, tool_calls


def save_uploaded_file(uploaded_file, memory_dir: Path) -> str:
    """Save an uploaded file to the memory directory."""
    file_path = memory_dir / uploaded_file.name
    file_path.parent.mkdir(parents=True, exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    return str(file_path.relative_to(memory_dir))


def main():
    st.set_page_config(page_title="Funes Agent UI", page_icon="🧠", layout="wide")

    st.title("🧠 Funes Agent Comparison")
    st.markdown("Compare baseline LLM responses with memory-augmented agent responses")

    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")

        # API Key input
        api_key = st.text_input(
            "OpenAI API Key", type="password", help="Enter your OpenAI API key"
        )

        # Model selection
        model = st.selectbox(
            "Select Model",
            OPENAI_MODELS,
            index=0,
            help="Choose the OpenAI model to use",
        )

        # Memory files section
        st.header("Memory Files")

        # File upload
        uploaded_files = st.file_uploader(
            "Upload files to memory",
            accept_multiple_files=True,
            type=["txt", "md"],
            help="Upload files that the agent can reference",
        )

        if uploaded_files:
            MEM_DIR.mkdir(exist_ok=True)
            for uploaded_file in uploaded_files:
                relative_path = save_uploaded_file(uploaded_file, MEM_DIR)
                st.success(f"Saved: {relative_path}")

        # Display current memory files
        if MEM_DIR.exists():
            try:
                memory_files = MEM_DIR.glob("**/*")
                memory_files = [
                    str(file.relative_to(MEM_DIR))
                    for file in memory_files
                    if file.is_file() and not file.name.startswith(".")
                ]
                memory_files.sort()
                if memory_files:
                    st.subheader("Current Memory Files")
                    for file in memory_files:
                        if st.button(f"📄 {file}", key=f"file_{file}"):
                            try:
                                content = (MEM_DIR / Path(file)).read_text(
                                    encoding="utf-8"
                                )
                                st.text_area(
                                    f"Contents of {file}",
                                    content,
                                    height=200,
                                    key=f"content_{file}",
                                )
                            except Exception as e:
                                st.error(f"Error reading {file}: {e}")
                else:
                    st.info("No memory files found")
            except Exception as e:
                st.error(f"Error listing memory files: {e}")

    # Main content area
    if not api_key:
        st.warning("Please enter your OpenAI API key in the sidebar to continue.")
        return

    # Prompt input
    prompt = st.text_area(
        "Enter your prompt",
        height=100,
        placeholder="Ask a question that might benefit from the memory files...",
        help="The agent will check memory files for relevant information",
    )

    if st.button("🚀 Generate Responses", type="primary"):
        if not prompt.strip():
            st.error("Please enter a prompt")
            return

        with st.spinner("Generating responses..."):
            try:
                # Create two columns for side-by-side comparison
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("🤖 Baseline Response")
                    with st.container():
                        baseline_response = get_base_response(prompt, model, api_key)
                        st.markdown(baseline_response)

                with col2:
                    st.subheader("🧠 Agent Response (with Memory)")
                    with st.container():
                        agent_response, tool_calls = asyncio.run(
                            get_agent_response(prompt, model, api_key)
                        )
                        st.markdown(agent_response)

                        if tool_calls:
                            st.subheader("🔧 Tool Calls Used")
                            for i, tool_call in enumerate(tool_calls, 1):
                                st.code(f"{i}. {tool_call['name']}")
                                if tool_call["arguments"]:
                                    title = f"Arguments for {tool_call['name']}"
                                    with st.expander(title):
                                        st.json(tool_call["arguments"])
                        else:
                            st.info("No tool calls were made")

            except Exception as e:
                st.error(f"Error generating responses: {e}")
                st.exception(e)


if __name__ == "__main__":
    main()
