from types import SimpleNamespace
from unittest.mock import Mock, patch

from minisweagent.models import GLOBAL_MODEL_STATS
from minisweagent.models.robust_litellm_model import RobustLitellmModel


def test_robust_litellm_model_extracts_chat_completion_content():
    model = RobustLitellmModel(model_name="mistral/devstral-2512", cost_tracking="ignore_errors")

    initial_cost = GLOBAL_MODEL_STATS.cost

    with patch("litellm.completion") as mock_completion:
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Hello from completion"))]
        mock_completion.return_value = mock_response

        with patch("litellm.cost_calculator.completion_cost", return_value=0.0):
            result = model.query([{"role": "user", "content": "test"}])

    assert result["content"] == "Hello from completion"
    assert model.n_calls == 1
    assert model.cost == 0.0
    assert GLOBAL_MODEL_STATS.cost == initial_cost


def test_robust_litellm_model_falls_back_to_responses_text_extraction():
    model = RobustLitellmModel(model_name="gpt-5-mini", cost_tracking="ignore_errors")

    initial_cost = GLOBAL_MODEL_STATS.cost

    with patch("litellm.completion") as mock_completion:
        # No choices attribute -> forces responses-text fallback.
        mock_response = SimpleNamespace(output_text="Hello from responses")
        mock_completion.return_value = mock_response

        with patch("litellm.cost_calculator.completion_cost", return_value=0.0):
            result = model.query([{"role": "user", "content": "test"}])

    assert result["content"] == "Hello from responses"
    assert model.n_calls == 1
    assert model.cost == 0.0
    assert GLOBAL_MODEL_STATS.cost == initial_cost


def test_robust_litellm_model_cleans_nonstandard_message_keys():
    model = RobustLitellmModel(model_name="mistral/devstral-2512", cost_tracking="ignore_errors")

    with patch("litellm.completion") as mock_completion:
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="ok"))]
        mock_completion.return_value = mock_response

        with patch("litellm.cost_calculator.completion_cost", return_value=0.0):
            model.query(
                [
                    {"role": "user", "content": "hi", "timestamp": "123", "extra": "nope"},
                ]
            )

        assert mock_completion.call_count == 1
        _kwargs = mock_completion.call_args.kwargs
        sent_messages = _kwargs["messages"]
        assert sent_messages == [{"role": "user", "content": "hi"}]
