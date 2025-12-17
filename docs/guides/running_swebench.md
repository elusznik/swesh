# Running SWE-bench Evaluation on mini-swe-agent

This guide covers how to set up and run SWE-bench evaluations using **live-swe-agent** with either **Docker** or **Podman**.

---

## 1. Prerequisites & Installation

### Python Environment
Install this repo (swesh) with full dependencies:
```bash
uv sync --extra full
```

### Container Runtime Setup

#### Option A: Docker (Standard)
1.  Install Docker Desktop or Engine.
2.  Ensure the docker daemon is running (`docker ps` should work).
3.  No extra configuration needed.

#### Option B: Podman (Daemonless/Rootless)
1.  Install Podman: `sudo apt install podman` (Linux) or `brew install podman` (Mac).
2.  **Enable Socket**: The SWE-bench *evaluation harness* requires a Docker-compatible socket.
    ```bash
    systemctl --user enable --now podman.socket
    ```
3.  **Set Environment**: Point the docker client to the Podman socket.
    ```bash
    export DOCKER_HOST=unix:///run/user/$(id -u)/podman/podman.sock
    ```
    *(Add this to your shell profile to make it permanent)*

---

## 2. Model Configuration

You need to configure the LLM that live-swe-agent will use. Create or edit your `.env` file (default location: `~/.config/mini-swe-agent/.env`).

### Step 1: Get API Keys
- **OpenAI**: Get key from [platform.openai.com](https://platform.openai.com).
- **Anthropic**: Get key from [console.anthropic.com](https://console.anthropic.com).
- **OpenRouter / Mistral**: Get key from [openrouter.ai](https://openrouter.ai) or [console.mistral.ai](https://console.mistral.ai).

### Step 2: Configure `.env`
Add the keys to your `.env` file:

```bash
# OpenAI
OPENAI_API_KEY=sk-...

# Anthropic
ANTHROPIC_API_KEY=sk-ant-...

# OpenRouter / Mistral / Other LiteLLM providers
MISTRAL_API_KEY=...
# Check https://docs.litellm.ai/docs/providers for the correct env var name for your provider
```

### Step 3: Verify Model Access
You can verify your model config by running a simple task:
```bash
# Example: Use Mistral via OpenRouter
uv run mini --model openrouter/mistralai/mistral-large-latest --task "Say hello"
```

---

## 3. Running the Agent (Generation)

This step runs the agent on SWE-bench instances to generate patches.

### Command Structure
```bash
uv run src/minisweagent/run/extra/swebench.py \
  --config config/livesweagent_swebench.yaml \
  --subset verified \
  --split test \
  --model <provider>/<model_name> \
  --slice <start>:<end> \
  [--environment-class podman] \
  --workers <N>
```

### Examples

**Run 1 instance with Docker + GPT-4o:**
```bash
uv run src/minisweagent/run/extra/swebench.py \
  --config config/livesweagent_swebench.yaml \
  --subset verified \
  --split test \
  --model openai/gpt-4o \
  --slice 0:1 \
  --workers 1
```

**Run 5 instances with Podman + Mistral Codestral:**
```bash
uv run src/minisweagent/run/extra/swebench.py \
  --config config/livesweagent_swebench.yaml \
  --subset verified \
  --split test \
  --model mistral/codestral-latest \
  --slice 0:5 \
  --environment-class podman \
  --workers 1
```

**Key Flags:**
- `--environment-class podman`: Required if using Podman. Omit for Docker.
- `--model`: Format is `provider/model-name` (e.g., `anthropic/claude-3-5-sonnet-20240620`).
- `--slice`: Range of instances (e.g., `0:25` for first 25).
- `--workers`: Number of parallel agents. **Keep to 1** for free/rate-limited APIs.

**Output:**
- `preds.json`: All generated patches collected here.
- `<instance_id>/`: Directory containing detailed logs and trajectories.

---

## 4. Verifying Results (Evaluation)

This step runs the official SWE-bench test suite against your `preds.json` to verify correctness.

```bash
uv run python -m swebench.harness.run_evaluation \
    --predictions_path preds.json \
    -d princeton-nlp/SWE-Bench_Verified \
    --run_id <your_run_name> \
    --max_workers 1
```

**Note for Podman Users**:
Ensure `DOCKER_HOST` is set correctly (see Prerequisites), otherwise the harness will fail with `FileNotFoundError` or `Connection refused`.

---

## Troubleshooting

- **Image Download Timeouts**:
  - We have increased the default timeout to **600s** (10 mins).
  - If you still time out, check your internet connection or pre-pull the images manually.
- **API Rate Limits (429)**:
  - If using free tier models, use `--workers 1` and anticipate occasional `429` errors.
  - Set `MSWEA_COST_TRACKING=ignore_errors` in `.env` if price fetching fails for exotic models.
- **"Connection Refused" (Evaluation)**:
  - Check if your docker/podman socket is active:
    - Docker: `systemctl status docker`
    - Podman: `systemctl --user status podman.socket`
