# Changes from upstream mini-swe-agent

- Baseline: upstream main, 2025-12-11 snapshot.
- Interactive REPL: inputs starting with `!` execute via subprocess then re-prompt. [src/minisweagent/agents/interactive.py](src/minisweagent/agents/interactive.py#L119-L141)
- Tests: coverage for single/multiple shell-escape commands and mixed regular input. [tests/agents/test_interactive_shell_escape.py](tests/agents/test_interactive_shell_escape.py)
- **Podman backend**: Added explicit `podman` environment class (`--environment-class podman`). [src/minisweagent/environments/podman.py](src/minisweagent/environments/podman.py)
- **Timeouts**: Increased default Docker `pull_timeout` to 600s to handle large SWE-bench images. [src/minisweagent/environments/docker.py](src/minisweagent/environments/docker.py)
- **Robust Model**: Added `RobustLitellmModel` to handle message cleaning (e.g. for Mistral) and robust cost tracking without modifying upstream `litellm_model.py`. [src/minisweagent/models/robust_litellm_model.py](src/minisweagent/models/robust_litellm_model.py)
- **Default Model**: Changed default model class in `__init__.py` to use `RobustLitellmModel` and updated `litellm` mapping. [src/minisweagent/models/__init__.py](src/minisweagent/models/__init__.py)
- **Dependencies**: Added `datasets` and `swebench` to project dependencies, and integrated `live-swe-agent` as a remote. [pyproject.toml](pyproject.toml)
- **Docs**: Added comprehensive guide for running SWE-bench with Podman/Docker. [docs/guides/running_swebench.md](docs/guides/running_swebench.md)
- **Type fixes**: Added `# type: ignore` comments to silence pre-existing type checker warnings in upstream code. This maintains compatibility while keeping the type checker happy.
- Other interactive/Textual agent behavior matches upstream at this snapshot.
