# Funes Agent UI

A web interface for comparing baseline LLM responses with memory-augmented agent responses.

## Features

- **Model Selection**: Choose from popular OpenAI models (GPT-4o, GPT-4-turbo, etc.)
- **Custom Prompts**: Enter any prompt to test both baseline and agent responses
- **Side-by-Side Comparison**: View responses from both the baseline model and memory-augmented agent
- **Memory File Management**: Upload and manage files that the agent can reference
- **Tool Call Visibility**: See which tools the agent used during its response
- **API Key Configuration**: Secure API key input for collaborators

## Quick Start

1. Install dependencies:
   ```bash
   pip install -e .
   ```

2. Start the UI:
   ```bash
   python run_ui.py
   ```
   
   Or if installed as a package:
   ```bash
   funes-ui
   ```

3. Open your browser to `http://localhost:8501`

4. Enter your OpenAI API key in the sidebar

5. Upload memory files or use existing ones in the `memory/` directory

6. Enter a prompt and click "Generate Responses"

## Usage Tips

- Upload relevant documents to the `memory/` directory before asking questions
- The agent will automatically check memory files for relevant information
- Supported file types: .txt, .md, .json, .csv, .py, .js, .html, .css
- View current memory files in the sidebar
- Tool calls show which memory functions the agent used

## Security

- API keys are only stored in memory during the session
- Files are saved to the local `memory/` directory
- No data is sent to external services except OpenAI's API