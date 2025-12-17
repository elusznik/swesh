from pathlib import Path
from unittest.mock import MagicMock, patch

import yaml

from minisweagent.agents.interactive import InteractiveAgent


def _load_default_agent_config() -> dict:
    config_path = Path("src/minisweagent/config/default.yaml")
    return yaml.safe_load(config_path.read_text())["agent"]


def test_shell_escape():
    """Test that shell escape commands (starting with !) are executed."""
    mock_model = MagicMock()
    mock_env = MagicMock()

    with (
        patch("minisweagent.agents.interactive.prompt_session") as mock_prompt_session,
        patch("minisweagent.agents.interactive.subprocess.run") as mock_run,
    ):
        mock_prompt_session.prompt.side_effect = ["!echo hello world", "/y"]

        agent = InteractiveAgent(mock_model, mock_env, **_load_default_agent_config())

        result = agent._prompt_and_handle_special("test prompt > ")

        mock_run.assert_called_once_with("echo hello world", shell=True)

        assert result == "/y"


def test_shell_escape_with_multiple_commands():
    """Test multiple shell escape commands in sequence."""
    mock_model = MagicMock()
    mock_env = MagicMock()

    with (
        patch("minisweagent.agents.interactive.prompt_session") as mock_prompt_session,
        patch("minisweagent.agents.interactive.subprocess.run") as mock_run,
    ):
        # After a bang-command, InteractiveAgent prompts again.
        # End with a mode switch command that doesn't recurse.
        mock_prompt_session.prompt.side_effect = ["!echo first", "!echo second", "/y"]

        agent = InteractiveAgent(mock_model, mock_env, **_load_default_agent_config())
        result = agent._prompt_and_handle_special("prompt > ")

        assert mock_run.call_count == 2
        mock_run.assert_any_call("echo first", shell=True)
        mock_run.assert_any_call("echo second", shell=True)
        assert result == "/y"


def test_shell_escape_with_regular_command():
    """Test mixing shell escape with regular commands."""
    mock_model = MagicMock()
    mock_env = MagicMock()

    with (
        patch("minisweagent.agents.interactive.prompt_session") as mock_prompt_session,
        patch("minisweagent.agents.interactive.subprocess.run") as mock_run,
    ):
        mock_prompt_session.prompt.side_effect = ["regular command", "/u"]

        agent = InteractiveAgent(mock_model, mock_env, **_load_default_agent_config())
        result = agent._prompt_and_handle_special("prompt > ")

        mock_run.assert_not_called()
        assert result == "regular command"
