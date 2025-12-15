# Bubblewrap Local Mode Security

**Goal**: Make bubblewrap the default for local (non-containerized) mode to prevent agent from accessing files outside the project directory.

## What Gets Restricted

| Path | Access | Rationale |
|------|--------|-----------|
| `/usr`, `/bin`, `/lib`, `/lib64` | Read-only | System binaries needed to run commands |
| `/etc` | Read-only | System config (timezone, resolv.conf, etc.) |
| `/proc`, `/dev` | Mounted fresh | Process info and devices |
| `/tmp` | Tmpfs (isolated) | Temp files, isolated per session |
| `$PROJECT_DIR` | **Read-write** | The only writable location |
| `~/.ssh`, `~/.aws`, `~/.config` | **No access** | Credentials - completely hidden |
| Rest of `$HOME` | **No access** | Protected from agent |

## Proposed Bubblewrap Args

```python
SECURE_LOCAL_ARGS = [
    "--unshare-user-try",
    # System directories (read-only)
    "--ro-bind", "/usr", "/usr",
    "--ro-bind", "/bin", "/bin",
    "--ro-bind", "/lib", "/lib",
    "--ro-bind", "/lib64", "/lib64",
    "--ro-bind", "/etc", "/etc",
    # Optional: allow pip/npm cache (read-only to prevent tampering)
    "--ro-bind-try", f"{HOME}/.cache", f"{HOME}/.cache",
    # Isolated temp
    "--tmpfs", "/tmp",
    # Required mounts
    "--proc", "/proc",
    "--dev", "/dev",
    "--new-session",
    # PATH
    "--setenv", "PATH", "/usr/local/bin:/usr/sbin:/usr/bin:/bin",
    # Project directory (the ONLY writable location)
    "--bind", PROJECT_DIR, PROJECT_DIR,
    "--chdir", PROJECT_DIR,
]
```

## What Agent CAN Do

- ✅ Run Python, Node, Go, any installed tool
- ✅ Read/write files in project directory
- ✅ Use pip/npm (packages go to project or temp)
- ✅ Access network (unless `--unshare-net` added)
- ✅ Read system config and libraries

## What Agent CANNOT Do

- ❌ Read `~/.ssh/id_rsa` or any SSH keys
- ❌ Read `~/.aws/credentials`
- ❌ Read `~/.config/` (API keys, tokens)
- ❌ Read `~/.bashrc`, `~/.zshrc`
- ❌ Modify anything outside project directory
- ❌ Access other projects or repos

## Implementation Plan

### 1. Create `SecureLocalEnvironment`

New file: `src/minisweagent/environments/secure_local.py`

```python
class SecureLocalEnvironment:
    """Local execution with bubblewrap isolation.
    
    Restricts agent to project directory only.
    Falls back to LocalEnvironment if bwrap unavailable.
    """
    
    def __init__(self, project_dir: str, ...):
        self.project_dir = Path(project_dir).resolve()
        if not self._bwrap_available():
            warn("bubblewrap not installed, running without isolation")
            # Fall back to LocalEnvironment
```

### 2. Make It Default

In environment selection logic:

```python
def get_environment(config: dict) -> Environment:
    env_class = config.get("environment_class", "secure_local")  # New default
    
    if env_class == "secure_local":
        return SecureLocalEnvironment(project_dir=os.getcwd())
    elif env_class == "local":
        return LocalEnvironment()  # Explicit unsafe mode
    ...
```

### 3. CLI Flags

```bash
# Default: secure local mode with bubblewrap
swesh --task "Fix the bug"

# Explicit unsafe local (matches Claude Code naming)
swesh --dangerously-skip-permissions --task "Fix the bug"

# Container mode (full isolation)
swesh --sandbox --task "Fix the bug"
```

## Dependencies

- **bubblewrap**: `apt install bubblewrap` or `dnf install bubblewrap`
- Most Linux distros have it available
- Not available on macOS (would need fallback)

## Fallback Behavior

| Condition | Behavior |
|-----------|----------|
| bwrap installed | Use SecureLocalEnvironment |
| bwrap missing | Warn + use LocalEnvironment |
| `--unsafe-local` flag | Skip bwrap, use LocalEnvironment |
| macOS/Windows | LocalEnvironment only (bwrap Linux-only) |

## 🚧 Status: To Be Implemented
