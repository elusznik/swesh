import logging

import litellm

from minisweagent.models import GLOBAL_MODEL_STATS
from minisweagent.models.litellm_model import LitellmModel
from minisweagent.models.utils.cache_control import set_cache_control
from minisweagent.models.utils.openai_utils import coerce_responses_text

logger = logging.getLogger("robust_litellm_model")


class RobustLitellmModel(LitellmModel):
    """
    A robust subclass of LitellmModel that adds:
    1. Message cleaning (removes extra keys like 'timestamp' that break Mistral/OpenRouter).
    2. Robust cost calc (allows 0 cost or missing cost without crashing if configured).
    """

    def _clean_message(self, message: dict) -> dict:
        """Clean message dictionary for API calls."""
        # Only keep keys that are part of the standard chat completion API
        valid_keys = {"role", "content", "name", "tool_calls", "tool_call_id"}
        return {k: v for k, v in message.items() if k in valid_keys}

    def query(self, messages: list[dict[str, str]], **kwargs) -> dict:
        if self.config.set_cache_control:
            messages = set_cache_control(messages, mode=self.config.set_cache_control)

        # Clean messages before sending
        cleaned_messages = [self._clean_message(m) for m in messages]

        # Call the parent's internal _query method with cleaned messages
        response = self._query(cleaned_messages, **kwargs)

        # Match stock LitellmModel behavior first (chat-completions shape),
        # then fall back to Responses API extraction.
        text = ""
        try:
            text = response.choices[0].message.content or ""  # type: ignore[attr-defined]
        except Exception:
            text = ""
        if not text:
            text = coerce_responses_text(response)

        # Robust cost calculation
        try:
            cost = litellm.cost_calculator.completion_cost(response, model=self.config.model_name)
            # We relax the strict > 0 check here or handle it gracefully
            if cost <= 0.0:
                logger.debug(f"Cost for {self.config.model_name} is {cost}")
        except Exception as e:
            if self.config.cost_tracking != "ignore_errors":
                raise RuntimeError(
                    f"Error calculating cost for model {self.config.model_name}: {e}. "
                    "You can ignore this with MSWEA_COST_TRACKING='ignore_errors'."
                ) from e
            cost = 0.0

        self.n_calls += 1
        self.cost += cost
        GLOBAL_MODEL_STATS.add(cost)

        model_dump = getattr(response, "model_dump", None)
        dumped_response = model_dump() if callable(model_dump) else {}

        return {
            "content": text,
            "extra": {
                "response": dumped_response,
                "cost": cost,
            },
        }
