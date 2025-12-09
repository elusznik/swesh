# Interactive Mini-SWE-Agent Guide

This repository has been enhanced with interactive features and fixes to support "Claude Code" style workflows and free OpenRouter models.

## 1. New Features

### Shell Escape (`!`)
You can now run shell commands directly from the interactive agent prompt (when it asks for confirmation/next step) by prefixing them with `!`.

*   **Usage**: `!ls -la` or `!git status`
*   **Result**: The command runs locally, output is displayed, and the prompt returns.

### Free Model Support (`:free`)
The agent now automatically detects free OpenRouter models (ending in `:free`) and disables strict cost tracking logic.
This prevents the `Error calculating cost... This model isn't mapped yet` crash.

*   **Supported Models**: `google/gemini-2.0-flash-exp:free`, `meta-llama/llama-3.3-70b-instruct:free`, etc.

## 2. Execution Modes

### Local Developer Mode (Default)
The standard `mini` command **ALWAYS** runs locally on your host machine. It is designed for "Live" usage on your current repository.

*   **Command**: `mini` or `python -m minisweagent.run.mini`
*   **Config**: `config/livesweagent.yaml`
*   **Safety**: Be careful! It can delete files on your machine.
*   **Environment**: Uses `LocalEnvironment` (ignores Docker settings in yaml).

### Docker Sandbox Mode
To run the agent in an isolated Docker container (safe for risky tasks or benchmarks), you must use the custom runner script.

*   **Command**: `uv run --with docker --with . python mini_docker.py`
*   **Config**: `config/livesweagent_swebench.yaml` (Used automatically by the script).
*   **Environment**: uses `DockerEnvironment`.
*   **Prerequisite**: Docker must be running.

## 3. Setup Shortcuts

### Setting the Model (Global)
```bash
# Set Global .env
PYTHONPATH=src uv run -m minisweagent.run.mini_extra config set MSWEA_MODEL_NAME "openrouter/google/gemini-2.0-flash-exp:free"

# Set API Key
PYTHONPATH=src uv run -m minisweagent.run.mini_extra config set OPENROUTER_API_KEY "sk-or-v1-..."
```

### Running Locally
```bash
PYTHONPATH=src uv run -m minisweagent.run.mini --config config/livesweagent.yaml
```
