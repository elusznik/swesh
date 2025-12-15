from unittest.mock import MagicMock, patch

from minisweagent.agents.interactive import InteractiveAgent


def test_bang_commands_pass_through():
    """Upstream InteractiveAgent treats '!cmd' like plain input."""
    mock_model = MagicMock()
    mock_env = MagicMock()

    with patch("minisweagent.agents.interactive.prompt_session.prompt", return_value="!echo hello"):
        agent = InteractiveAgent(mock_model, mock_env)
        result = agent._prompt_and_handle_special("prompt > ")

    assert result == "!echo hello"


def test_mode_commands_switch_and_return():
    mock_model = MagicMock()
    mock_env = MagicMock()

    with patch("minisweagent.agents.interactive.prompt_session.prompt", side_effect=["/y", "/c", "/u"]):
        agent = InteractiveAgent(mock_model, mock_env)

        assert agent.config.mode == "confirm"
        assert agent._prompt_and_handle_special("prompt > ") == "/y"
        assert agent.config.mode == "yolo"

        assert agent._prompt_and_handle_special("prompt > ") == "/c"
        assert agent.config.mode == "confirm"

        assert agent._prompt_and_handle_special("prompt > ") == "/u"
        assert agent.config.mode == "human"
