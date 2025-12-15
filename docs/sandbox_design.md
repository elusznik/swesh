# Sandbox Mode Design

This document explores approaches for running swesh in an isolated container while working on local repositories.

## Goals

1. **Safety**: Prevent agent from modifying host filesystem accidentally
2. **Convenience**: Work on any project without manual container setup
3. **Speed**: Minimize overhead from container operations

---

## ⚠️ Critical Design Principle

**The agent should start in a READY environment, not spend tokens on setup.**

SWE-bench images are pre-configured: Python installed, deps present, repo cloned. The agent immediately focuses on the task. If we make the agent discover and install tools, we waste tokens and risk failures.

**Solution**: All setup happens **BEFORE** the agent loop starts.

```
┌─────────────────────────────────────────────────────────────┐
│  BEFORE agent starts (swesh handles this automatically):   │
│  1. Copy repo to container                                 │
│  2. Detect project type (Python? Node? Rust?)              │
│  3. Install runtime + dependencies                         │
│  4. Verify setup worked                                    │
└─────────────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│  THEN agent starts (in ready-to-code environment):         │
│  - All tools installed                                     │
│  - Dependencies present                                    │
│  - Same experience as SWE-bench                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚧 Future Considerations (Not Implementing Now)

The ideas below are documented for future reference but are **out of scope** for the initial implementation.

### Devcontainer Support

If `.devcontainer/devcontainer.json` exists, use that image directly. However, most projects don't have this — it's mainly VS Code/Codespaces ecosystems.

### Auto-Detection Implementation

Hard-coded detection for common languages:

```python
def _setup_project(self):
    repo_files = self._list_files("/workspace")
    
    if "requirements.txt" in repo_files:
        self.execute("apt-get install -y python3 python3-pip")
        self.execute("pip install -r requirements.txt")
    elif "package.json" in repo_files:
        self.execute("curl -fsSL https://deb.nodesource.com/setup_20.x | bash -")
        self.execute("apt-get install -y nodejs && npm install")
    elif "Cargo.toml" in repo_files:
        self.execute("curl https://sh.rustup.rs | sh -s -- -y && cargo fetch")
    # ... etc for go.mod, Gemfile, pom.xml
```

**Problem**: Growing maintenance burden. Every language needs install commands that can change.

### Setup Script Convention

Look for project-provided setup instead:

```bash
if [ -f setup.sh ]; then ./setup.sh
elif make -q setup 2>/dev/null; then make setup
fi
```

Puts burden on project to know how to set itself up. More scalable but requires project cooperation.

### Options Summary

| Option | Pros | Cons |
|--------|------|------|
| Hard-code ~10 languages | Works immediately | Maintenance burden |
| setup.sh/Makefile convention | Scalable | Requires project buy-in |
| Devcontainer support | Perfect match | Rarely present |

---

## Approach 1: Auto-Setup Before Agent Starts

**swesh** detects project type and installs deps BEFORE the agent loop begins.

### How It Works

1. User runs `mini --sandbox`
2. swesh copies repo to container
3. swesh detects project files and runs installs:
   - `requirements.txt` → `apt install python3 && pip install -r requirements.txt`
   - `package.json` → `apt install nodejs npm && npm install`
   - `Cargo.toml` → install rustup, `cargo build`
   - etc.
4. **THEN** agent starts with everything ready

### Detection Table

| File | Runtime Install | Dep Install |
|------|-----------------|-------------|
| `requirements.txt` | `apt install python3 python3-pip` | `pip install -r requirements.txt` |
| `pyproject.toml` | `apt install python3 python3-pip` | `pip install -e .` |
| `package.json` | `curl -fsSL nodejs.org | bash` | `npm install` |
| `Cargo.toml` | `curl rustup.rs \| sh` | `cargo fetch` |
| `go.mod` | `apt install golang` | `go mod download` |
| `Gemfile` | `apt install ruby` | `bundle install` |
| `.devcontainer/` | Use devcontainer image | (handled by image) |

### Devcontainer Support (Best Case)

Many projects already have `.devcontainer/devcontainer.json`:

```json
{
  "image": "mcr.microsoft.com/devcontainers/rust:1-bullseye"
}
```

If present, swesh uses that image directly — zero detection needed, guaranteed compatible.



### Base Image

```dockerfile
FROM ubuntu:24.04

# Core essentials only
RUN apt-get update && apt-get install -y \
    sudo git curl wget \
    build-essential \
    ca-certificates

# Create non-root user with sudo
RUN useradd -m -s /bin/bash agent && \
    echo "agent ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers

USER agent
WORKDIR /workspace
```

**Size**: ~200MB (vs 2-3GB for "everything")

### Examples of Agent Self-Installing

When the agent sees a Python project:
```bash
# Agent's first command
sudo apt install -y python3 python3-pip && pip install -r requirements.txt
```

When it sees Rust:
```bash
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && cargo build
```

When it sees Elixir, Zig, Nim, Julia, or any other language:
```bash
# Agent figures it out - it's an LLM, it knows how to install things
```

### Prompt Enhancement (Optional)

Add to sandbox system prompt:

```text
You are running in a fresh Ubuntu container. If you need any language runtimes 
or tools, install them first using apt, curl, or the language's official installer.
```

---

## Approach 2: Project Directory Copy

Copy the local repo into a container, auto-detect deps, install them.

### How it Works

1. Start container from base image
2. `docker cp ./repo container:/workspace`
3. Detect `requirements.txt`, `package.json`, etc.
4. Run appropriate install command
5. Agent works in `/workspace`
6. On exit: `docker cp container:/workspace ./repo` (sync back)

### Auto-Detection Logic

```python
INSTALL_COMMANDS = {
    "requirements.txt": "pip install -r requirements.txt",
    "pyproject.toml": "pip install -e .",
    "package.json": "npm install",
    "Cargo.toml": "cargo build",
    "go.mod": "go mod download",
    "Gemfile": "bundle install",
    "pom.xml": "mvn dependency:resolve",
    "build.gradle": "gradle dependencies",
}
```

---

## Approach 3: Volume Mount (Simplest)

Bind-mount the local directory instead of copying.

```bash
podman run -v $(pwd):/workspace:Z -w /workspace swesh-sandbox:latest
```

**Pros**: No copy overhead, changes appear instantly
**Cons**: Less isolation (agent writes directly to host)

### Hybrid: Copy-on-Write

Use an overlay filesystem:
- Base layer: read-only mount of host repo
- Top layer: writable container layer
- User chooses to accept/reject changes

---

## Comparison

| Approach | Isolation | Speed | Complexity | Any Language? |
|----------|-----------|-------|------------|---------------|
| Minimal Base + On-Demand | Full | Medium* | Low | ✅ Yes |
| Dir Copy + Sync | Full | Slow (large repos) | Medium | ✅ Yes |
| Volume Mount | Partial | Fast | Low | ✅ Yes |
| Copy-on-Write | Full | Fast | High | ✅ Yes |

*First run slower due to apt installs; subsequent runs can reuse container.

---

## Recommended MVP

1. **Minimal base image** (~200MB Ubuntu with sudo/git/curl)
2. **Agent installs runtimes on-demand** (Python, Rust, Go, whatever)
3. **Directory copy for isolation** (sync back on exit)

Future: Container reuse to cache installed runtimes.

---

## CLI Usage (Proposed)

```bash
# Run in sandbox with auto-detected image
mini --sandbox --task "Fix the login bug"

# Run with custom image (pre-built with deps)
mini --sandbox --image myproject:dev --task "Add feature X"

# Run without sync-back (discard changes on exit)
mini --sandbox --no-sync --task "Experiment with refactoring"
```
