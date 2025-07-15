# Funes 🧠

## Installation

### Prerequisites

- Python 3.9 or higher
- OpenAI API key

### Setup

1. Clone or download the repository:
```bash
cd funes
```

2. Install dependencies using uv (recommended) or pip:
```bash
# Using uv (if installed)
uv sync

# Or using pip
pip install -e .
```

3. Set up your OpenAI API key:
   - You can enter it directly in the web interface
   - Or set it as an environment variable: `export OPENAI_API_KEY=your_key_here`
   - or put it in a `.env` file, with a line: `OPENAI_API_KEY=your_key_here`

## Usage

### Web Interface

Launch the Streamlit web interface:

```bash
uv run funes-ui
```

Or run directly:

```bash
python run_ui.py
```

The interface will open in your browser at `http://localhost:8501`.

### Example Memory Files
You can put memory files directly in the `memory/` directory instead of or in addition to uploading them through the web interface. These are not under version-control. You'll have to move them away if you want to "forget" them.

```
memory/
├── diet.md              # "I am a vegetarian."
├── programming.md       # "I prefer working in Python and SQL."
```

## Available Tools

The agent has access to these specialized tools:

- **`list_memory_files()`**: Lists all files in the memory directory
- **`read_memory_file(path)`**: Reads the content of a specific memory file
