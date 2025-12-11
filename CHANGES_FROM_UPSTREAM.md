# Changes from upstream mini-swe-agent

- Baseline: upstream main, 2025-12-11 snapshot.
- Interactive REPL: inputs starting with `!` execute via subprocess then re-prompt. [src/minisweagent/agents/interactive.py](src/minisweagent/agents/interactive.py#L119-L141)
- Tests: coverage for single/multiple shell-escape commands and mixed regular input. [tests/agents/test_interactive_shell_escape.py](tests/agents/test_interactive_shell_escape.py)
- Other interactive/Textual agent behavior matches upstream at this snapshot.
