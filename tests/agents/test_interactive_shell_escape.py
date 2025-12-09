from unittest.mock import MagicMock, patch

from minisweagent.agents.interactive import InteractiveAgent


def test_shell_escape():
    """Test that shell escape commands (starting with !) are executed."""
    # Mock dependencies
    mock_model = MagicMock()
    mock_env = MagicMock()
    
    with (
        patch("minisweagent.agents.interactive.prompt_session") as mock_prompt_session,
        patch("minisweagent.agents.interactive.subprocess.run") as mock_run,
    ):
        # Setup mock prompt to return shell command then exit command
        mock_prompt_session.prompt.side_effect = ["!echo hello world", "/y"]
        
        # Create agent
        agent = InteractiveAgent(mock_model, mock_env)
        
        # Call the method that handles special commands
        result = agent._prompt_and_handle_special("test prompt > ")
        
        # Verify shell command was executed
        mock_run.assert_called_once_with("echo hello world", shell=True)
        
        # Verify method returns the next command (which switches mode)
        assert result == "/y"


def test_shell_escape_with_multiple_commands():
    """Test multiple shell escape commands in sequence."""
    mock_model = MagicMock()
    mock_env = MagicMock()
    
    with (
        patch("minisweagent.agents.interactive.prompt_session") as mock_prompt_session,
        patch("minisweagent.agents.interactive.subprocess.run") as mock_run,
    ):
        mock_prompt_session.prompt.side_effect = ["!echo first", "!echo second", "/c"]
        
        agent = InteractiveAgent(mock_model, mock_env)
        result = agent._prompt_and_handle_special("prompt > ")
        
        # Should have called run twice
        assert mock_run.call_count == 2
        mock_run.assert_any_call("echo first", shell=True)
        mock_run.assert_any_call("echo second", shell=True)
        assert result == "/c"


def test_shell_escape_with_regular_command():
    """Test mixing shell escape with regular commands."""
    mock_model = MagicMock()
    mock_env = MagicMock()
    
    with (
        patch("minisweagent.agents.interactive.prompt_session") as mock_prompt_session,
        patch("minisweagent.agents.interactive.subprocess.run") as mock_run,
    ):
        mock_prompt_session.prompt.side_effect = ["regular command", "/u"]
        
        agent = InteractiveAgent(mock_model, mock_env)
        result = agent._prompt_and_handle_special("prompt > ")
        
        # Should not call subprocess.run for regular commands
        mock_run.assert_not_called()
        assert result == "regular command"
