# OpenMemory Fork

OpenMemory is [Mem0's](https://github.com/mem0ai/mem0) open source, local MCP server for maintaining a structured database of memories accessible via LLM agents. It supports features like memory creation and retrieval, per-application memory permissions, and access logging. This fork is for hacking on integration with Funes, focused on:

- Broader client-side support (especially local LMs)
- Local or offloaded LM and embedding operations (i.e., removing OpenAI requirement)
- Remote (federated) deployment

Original docs [here](https://github.com/mem0ai/mem0/tree/main/openmemory).

## Setup

You can quickly run OpenMemory with `./run.sh`, if your `.env` file has an `OPENAI_API_KEY`.

You can also set the `OPENAI_API_KEY` as a parameter to the script:

```bash
./run.sh | OPENAI_API_KEY=your_api_key bash
```

Then stop the server with `./stop.sh`.

### Prerequisites

- Docker and Docker Compose
- Python 3.9+ (for backend development)
- Node.js (for frontend development)
- OpenAI API Key (required for LLM interactions, run `cp api/.env.example api/.env` then change **OPENAI_API_KEY** to yours)

### Client-side setup

#### Claude

With the OpenMemory server running, use `npx @openmemory/install local http://localhost:8765/mcp/claude/sse/nrh146 --client claude`. This will add the following entry to your `claude_desktop_config.json`:

```json
"openmemory-local": {
      "command": "npx",
      "args": [
        "-y",
        "supergateway",
        "--sse",
        "http://localhost:8765/mcp/claude/sse/nrh146"
      ]
    }
```

Then, openmemory should be available as a tool within Claude. 

Here's an example of a thread that [creates a memory](https://claude.ai/share/b6d647bc-2c0d-4d9e-a1e0-f6326e4c8428), and one that [accesses a memory](https://claude.ai/share/5eb4f568-7e7b-43b7-9565-5ce67c0b8b15).

#### LMStudio
Follow the steps in [this release post](https://lmstudio.ai/blog/lmstudio-v0.3.17) to add the same entry to your LMStudio `mcp.json`. Any model trained for tool use should be able to leverage the OpenMemory server. 

