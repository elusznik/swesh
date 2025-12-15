import unittest

from livesweagent.ui.parse.transcript import messages_to_transcript, parse_assistant_message


class TranscriptParsingTests(unittest.TestCase):
    def test_parse_assistant_message_splits_thought_and_bash(self) -> None:
        msg = "THOUGHT: do a thing\n\n```bash\necho hi\n```\n"
        items = parse_assistant_message(msg)
        self.assertEqual([i.type for i in items], ["assistant_reasoning", "tool_call"])
        self.assertTrue(items[0].text.startswith("THOUGHT:"))
        self.assertEqual(items[1].text, "echo hi")

    def test_parse_assistant_message_malformed_falls_back(self) -> None:
        msg = "```bash\necho a\n```\n```bash\necho b\n```"
        items = parse_assistant_message(msg)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].type, "assistant_output")

    def test_messages_to_transcript_classifies_observations(self) -> None:
        messages = [
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "task here"},
            {"role": "assistant", "content": "THOUGHT: x\n```bash\nls\n```"},
            {"role": "user", "content": "Observation: {'returncode': 0, 'output': 'ok'}"},
            {"role": "user", "content": "LimitsExceeded"},
        ]

        transcript = messages_to_transcript(messages)
        self.assertEqual(
            [t.type for t in transcript],
            ["user_input", "assistant_reasoning", "tool_call", "tool_output", "system"],
        )


if __name__ == "__main__":
    unittest.main()
