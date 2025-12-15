import re
from unittest.mock import patch

import pytest

from minisweagent.models.test_models import DeterministicModel
from minisweagent.run.github_issue import DEFAULT_CONFIG, main


def normalize_outputs(s: str) -> str:
    """Strip leading/trailing whitespace and normalize minor formatting differences."""
    # Remove everything between <args> and </args>, because this contains docker container ids
    s = re.sub(r"<args>(.*?)</args>", "", s, flags=re.DOTALL)
    # Normalize cases where </output> is placed on same line
    s = re.sub(r"(?<!\n)</output>", "\n</output>", s)
    # Replace all lines that have root in them because they tend to appear with times
    s = "\n".join(l for l in s.split("\n") if "root root" not in l)
    # Some environments omit a final blank line before </output>.
    s = re.sub(r"\n\n</output>$", "\n</output>", s.strip())
    return "\n".join(line.rstrip() for line in s.strip().split("\n"))


def assert_observations_match(expected_observations: list[str], messages: list[dict]) -> None:
    """Compare expected observations with actual observations from agent messages

    Args:
        expected_observations: List of expected observation strings
        messages: Agent conversation messages (list of message dicts with 'role' and 'content')
    """
    # Extract actual observations from agent messages
    # User messages (observations) are at indices 3, 5, 7, etc.
    actual_observations = []
    for i in range(len(expected_observations)):
        user_message_index = 3 + (i * 2)
        assert messages[user_message_index]["role"] == "user"
        actual_observations.append(messages[user_message_index]["content"])

    assert len(actual_observations) == len(expected_observations), (
        f"Expected {len(expected_observations)} observations, got {len(actual_observations)}"
    )

    for i, (expected_observation, actual_observation) in enumerate(zip(expected_observations, actual_observations)):
        normalized_actual = normalize_outputs(actual_observation)
        normalized_expected = normalize_outputs(expected_observation)

        assert normalized_actual == normalized_expected, (
            f"Step {i + 1} observation mismatch:\nExpected: {repr(normalized_expected)}\nActual: {repr(normalized_actual)}"
        )


def test_configure_if_first_time_called():
    """Test that configure_if_first_time is called when running github_issue main."""
    with (
        patch("minisweagent.run.github_issue.configure_if_first_time") as mock_configure,
        patch("minisweagent.run.github_issue.fetch_github_issue") as mock_fetch,
        patch("minisweagent.run.github_issue.InteractiveAgent") as mock_agent,
        patch("minisweagent.run.github_issue.get_model"),
        patch("minisweagent.run.github_issue.DockerEnvironment"),
        patch("minisweagent.run.github_issue.yaml.safe_load") as mock_yaml_load,
        patch("minisweagent.run.github_issue.get_config_path") as mock_get_config_path,
        patch("minisweagent.run.github_issue.save_traj"),
    ):
        mock_fetch.return_value = "Test issue"
        mock_yaml_load.return_value = {"agent": {}, "environment": {}, "model": {}}
        mock_get_config_path.return_value.read_text.return_value = "test config"
        mock_agent_instance = mock_agent.return_value
        mock_agent_instance.run.return_value = (0, "success")
        mock_agent_instance.env.execute.return_value = None

        main(issue_url="https://github.com/test/repo/issues/1", config=DEFAULT_CONFIG, model="test-model", yolo=True)

        mock_configure.assert_called_once()


class ReplayEnvironment:
    def __init__(self, expected_user_messages: list[str], *, ignore_command_prefixes: tuple[str, ...] = ()):
        self._expected_user_messages = expected_user_messages
        self._ignore_command_prefixes = ignore_command_prefixes
        self._idx = 0

    def get_template_vars(self) -> dict:
        return {}

    def execute(self, command: str, cwd: str = "") -> dict[str, object]:
        if any(command.startswith(prefix) for prefix in self._ignore_command_prefixes):
            return {"returncode": 0, "output": ""}

        if self._idx >= len(self._expected_user_messages):
            raise AssertionError(f"ReplayEnvironment ran out of expected outputs at command: {command!r}")

        expected = self._expected_user_messages[self._idx]
        self._idx += 1

        match = re.search(
            r"<returncode>(?P<rc>\d+)</returncode>\s*\n<output>\n(?P<out>.*?)(?:\n</output>|</output>)\s*$",
            expected,
            re.DOTALL,
        )
        if match is not None:
            return {"returncode": int(match.group("rc")), "output": match.group("out")}

        # Final message is the Submitted payload (diff), not an observation.
        return {"returncode": 0, "output": f"MINI_SWE_AGENT_FINAL_OUTPUT\n{expected}"}


@pytest.mark.slow
def test_github_issue_end_to_end(github_test_data):
    """Test the complete flow from CLI to final result using deterministic IO."""

    model_responses = github_test_data["model_responses"]
    expected_observations = github_test_data["expected_observations"]

    with (
        patch("minisweagent.run.github_issue.configure_if_first_time"),
        patch("minisweagent.run.github_issue.fetch_github_issue", return_value="Test issue"),
        patch("minisweagent.run.github_issue.get_model") as mock_get_model,
        patch(
            "minisweagent.run.github_issue.DockerEnvironment",
            return_value=ReplayEnvironment(expected_observations, ignore_command_prefixes=("git clone ",)),
        ),
        patch("minisweagent.run.github_issue.save_traj"),
        patch("minisweagent.agents.interactive.prompt_session.prompt", return_value=""),  # No new task
    ):
        mock_get_model.return_value = DeterministicModel(outputs=model_responses)
        github_url = "https://github.com/SWE-agent/test-repo/issues/1"
        agent = main(issue_url=github_url, model="tardis", config=DEFAULT_CONFIG, yolo=True)  # type: ignore

    assert agent is not None
    messages = agent.messages

    assert_observations_match(expected_observations, messages)

    # The fixture includes additional model outputs beyond the point where
    # COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT triggers a stop.
    assert agent.model.n_calls <= len(model_responses)
