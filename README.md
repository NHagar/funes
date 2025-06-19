# MemChat

**Transparent, memory-aware chat sandbox for rapid LLM prototyping**

MemChat provides side-by-side comparison of OpenAI model responses with and without access to your local memory files, making it easy to see exactly when and how external context influences AI responses.

## Features

- 🔄 **Side-by-side comparison**: See baseline vs memory-augmented responses
- 📁 **Simple memory system**: Drop text/markdown files in `./memory/` folder
- 🔍 **Tool call transparency**: Real-time log of every file access
- 🎯 **Zero setup**: Single `pipx install` command
- 💻 **Dual interface**: Interactive TUI or headless CLI mode
- 📊 **Export options**: JSON output and diff views

## Quick Start

### Installation

```bash
# Install with pipx (recommended)
pipx install .

# Or install with pip
pip install .
```

### Basic Usage

1. **Create memory files**:
   ```bash
   mkdir memory
   echo "My project uses React and TypeScript" > memory/tech-stack.txt
   echo "The main API endpoint is /api/v2/" > memory/api-info.txt
   ```

2. **Launch interactive TUI**:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   memchat
   ```

3. **Or use headless mode**:
   ```bash
   memchat --prompt "How should I structure my API routes?" --model gpt-4o-mini
   ```

## Usage Examples

### Interactive TUI Mode

Launch the full TUI interface:

```bash
memchat
```

- Select your preferred OpenAI model from the dropdown
- Enter prompts in the bottom input field
- Watch real-time tool calls in the log table
- Compare baseline vs memory-augmented responses side-by-side

### Headless CLI Mode

Quick one-off queries:

```bash
# Basic usage
memchat --prompt "What's my tech stack?" --model gpt-4o-mini

# Custom memory directory
memchat --prompt "Explain the codebase" --memory ./docs/

# JSON output for scripting
memchat --prompt "Summarize the project" --json

# Show diff between responses
memchat --prompt "What libraries do I use?" --diff

# List available models
memchat --list-models
```

### CLI Options

| Option | Description | Default |
|--------|-------------|---------|
| `--prompt, -p` | Chat prompt to process | Launches TUI if not provided |
| `--model, -m` | OpenAI model to use | `gpt-4o-mini` |
| `--memory` | Path to memory directory | `./memory` |
| `--json` | Output results as JSON | `false` |
| `--diff` | Show diff between responses | `false` |
| `--list-models` | List available OpenAI models | `false` |

## Memory File Format

MemChat works with any UTF-8 text files in your memory directory:

```
memory/
├── project-overview.md
├── api-documentation.txt
├── coding-standards.md
└── team-notes/
    ├── meeting-notes.txt
    └── decisions.md
```

The AI agent can:
- List all available memory files
- Read any file's contents when relevant to your prompt
- Access files recursively in subdirectories

## Development

### Setup

```bash
git clone <repository-url>
cd memchat

# Install in development mode
pipx install --editable .

# Install dev dependencies
pip install -e .[dev]
```

### Testing

```bash
# Run tests
pytest

# Run linting
ruff check .
ruff format .

# Type checking (if using mypy)
mypy memchat/
```

### Project Structure

```
memchat/
├── memchat/              # Main package
│   ├── __init__.py       # Package metadata
│   ├── cli.py           # Command-line interface  
│   ├── tui.py           # Textual TUI application
│   ├── orchestrator.py  # Chat orchestration logic
│   └── tools.py         # Memory file tools
├── tests/               # Test suite
│   ├── fixtures/        # Test data
│   └── test_*.py        # Test modules
├── pyproject.toml       # Package configuration
└── README.md           # This file
```

## How It Works

1. **Baseline Run**: MemChat first calls OpenAI's API without any tools, giving you the "raw" model response

2. **Augmented Run**: Then it runs the same prompt with memory tools available, allowing the AI to:
   - List files in your memory directory
   - Read specific files when they seem relevant
   - Incorporate that context into its response

3. **Comparison**: You see both responses side-by-side, plus a detailed log of exactly which files were accessed and when

This transparency helps you understand:
- When external context actually improves responses
- Which files are most relevant for different types of queries  
- How to structure your memory files for maximum effectiveness

## Requirements

- Python ≥ 3.9
- OpenAI API key (set `OPENAI_API_KEY` environment variable)
- Terminal with Unicode support for best TUI experience

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run linting and tests
5. Submit a pull request

For bugs and feature requests, please open an issue on GitHub.