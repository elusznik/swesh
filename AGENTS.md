# AGENTS.md

## Project Context & Origin
This repository (`swesh`) is an evolution of **Live-SWE-agent** and **mini-swe-agent**.
- **Origin**: It builds upon the minimalist `mini-swe-agent` framework and the self-evolving capabilities of `Live-SWE-agent`.
- **Goal**: To transform these research-focused prototypes into a polished, **interactive CLI tool** for software engineering (similar in UX to Claude Code, Codex CLI, or Gemini CLI).
- **Philosophy**: The agent should act as a "pair programmer" rather than a batch-process solver. It retains the capability to create its own tools (self-evolution) but operates within a user-facing read-eval-print loop.

## Codebase Structure
The repository contains source code from both component projects:
- **Root Directory**: Contains `Live-SWE-agent` scripts (e.g., `analyze_issue.py`, `explore_tool.py`, `fix_test_tool.py`, `run_test.py`) which operate directly in the workspace.
- **`src/minisweagent/`**: Contains the foundational `mini-swe-agent` package source code.
- **`src/livesweagent/`**: (Proposed) Location for the new interactive CLI implementation.
- **Configuration**: Global configurations reside in `config/` and project management in `pyproject.toml`.

## Technical Instructions for Agents & Developers
### 1. Environment & Package Management
You **MUST** use **`uv`** for all Python environment and package management tasks.
- **Do not** use `pip` or `virtualenv` directly unless absolutely necessary.
- **Running Code**: Use `uv run <script>` to execute Python scripts.
- **Installing Dependencies**: Use `uv add <package>` to add dependencies.
- **Syncing**: Use `uv sync` to ensure the environment matches the lockfile.

### 2. Operational Constraints
- **Preserve Existing Configurations**: Do not modify the original `mini-swe-agent` or `live-swe-agent` logic unless specifically refactoring for the interactive CLI goal.
- **Tooling**: When creating new tools or scripts, ensure they are compatible with the `uv` environment.

## Agent Architectures & Inspirations
This project draws inspiration from and aims to bridge the gap between several state-of-the-art agent architectures:

### Live-SWE-Agent (Interactive)
*   **Goal**: Transform the benchmark-focused `live-swe-agent` into a user-facing interactive CLI tool.
*   **Key Features**:
    *   **Runtime Self-Evolution**: The agent can write its own tools (Python scripts) on the fly to solve specific problems.
    *   **Human-in-the-loop**: Unlike the benchmark version, this interactive mode acts as a "pair programmer," engaging in a read-eval-print loop (REPL) with the user.
    *   **State Persistence**: Maintains project memory and tool definitions across sessions.

### Claude Code (Anthropic)
*   **Philosophy**: "Project Memory" and "Hidden Execution."
*   **Key Features**:
    *   **`CLAUDE.md`**: A root-level file that serves as a "Readme for Robots," injecting critical project context into every session.
    *   **Context Management**: Aggressive summarization and "squashing" of history to maintain long-term coherence without hitting token limits.

### OpenAI Codex CLI
*   **Philosophy**: "Skeletonization" and efficient context usage.
*   **Key Features**:
    *   **`AGENTS.md`**: Similar to `CLAUDE.md`, providing instructions for AI agents.
    *   **Code Skeletonizing**: Reading only the definitions (classes, functions) of large files to understand structure without consuming tokens on implementation details.

### Gemini CLI
*   **Philosophy**: Massive context window and "Infinite Scroll."
*   **Key Features**:
    *   **Context Caching**: Caching the static parts of the repository to reduce latency and cost.
    *   **Long-Context Reasoning**: Leveraging large context windows (1M+ tokens) to maintain the entire conversation history where possible.

### Copilot
*   **Philosophy**: Seamless IDE integration.
*   **Key Features**:
    *   **Context Awareness**: Deeply integrated into the editor to understand the user's active file and cursor position.
