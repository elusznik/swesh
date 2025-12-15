"""Opencode-style Textual UI for mini-swe-agent.

Implemented with lazy imports to keep this module importable in minimal
environments (e.g. docs builds / static analysis), while still using Textual at
runtime when dependencies are installed.

This lives under `livesweagent/` to preserve upstream mergeability.
"""

from __future__ import annotations

import importlib
import logging
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal


def create_opencode_textual_agent(model: Any, env: Any, **agent_kwargs: Any) -> Any:
    """Create an opencode-style Textual agent instance."""

    default_mod = importlib.import_module("minisweagent.agents.default")
    AgentConfig = getattr(default_mod, "AgentConfig")
    DefaultAgent = getattr(default_mod, "DefaultAgent")
    NonTerminatingException = getattr(default_mod, "NonTerminatingException")
    Submitted = getattr(default_mod, "Submitted")

    Spinner = importlib.import_module("rich.spinner").Spinner
    Text = importlib.import_module("rich.text").Text

    textual_app = importlib.import_module("textual.app")
    textual_binding = importlib.import_module("textual.binding")
    textual_containers = importlib.import_module("textual.containers")
    textual_query = importlib.import_module("textual.css.query")
    textual_events = importlib.import_module("textual.events")
    textual_screen = importlib.import_module("textual.screen")
    textual_widgets = importlib.import_module("textual.widgets")

    App = getattr(textual_app, "App")
    ComposeResult = getattr(textual_app, "ComposeResult")
    SystemCommand = getattr(textual_app, "SystemCommand")

    Binding = getattr(textual_binding, "Binding")

    Container = getattr(textual_containers, "Container")
    Vertical = getattr(textual_containers, "Vertical")
    VerticalScroll = getattr(textual_containers, "VerticalScroll")

    NoMatches = getattr(textual_query, "NoMatches")

    Key = getattr(textual_events, "Key")

    Screen = getattr(textual_screen, "Screen")

    Footer = getattr(textual_widgets, "Footer")
    Header = getattr(textual_widgets, "Header")
    Input = getattr(textual_widgets, "Input")
    Static = getattr(textual_widgets, "Static")
    TextArea = getattr(textual_widgets, "TextArea")

    @dataclass
    class OpencodeTextualAgentConfig(AgentConfig):
        mode: Literal["confirm", "yolo", "human"] = "confirm"
        whitelist_actions: list[str] = field(default_factory=list)
        confirm_exit: bool = True

    class _OpencodeAgent(DefaultAgent):
        def __init__(self, app: "OpencodeTextualAgent", *args: Any, **kwargs: Any):
            self.app = app
            super().__init__(*args, config_class=OpencodeTextualAgentConfig, **kwargs)
            self._current_action_from_human = False

        def add_message(self, role: str, content: str, **kwargs: Any):
            super().add_message(role, content, **kwargs)
            if self.app.agent_state != "UNINITIALIZED":
                self.app.call_from_thread(self.app.on_message_added)

        def query(self) -> dict:
            if self.config.mode == "human":
                human_input = self.app.input_bar.request_input("Enter your command:")
                self._current_action_from_human = True
                msg = {"content": f"\n```bash\n{human_input}\n```"}
                self.add_message("assistant", msg["content"])
                return msg

            self._current_action_from_human = False
            return super().query()

        def execute_action(self, action: dict) -> dict:
            if self.config.mode == "human" and not self._current_action_from_human:
                raise NonTerminatingException("Command not executed because user switched to manual mode.")

            if self.config.mode == "confirm" and action["action"].strip():
                if not any(re.match(pattern, action["action"]) for pattern in self.config.whitelist_actions):
                    result = self.app.input_bar.request_input(
                        "Press ENTER to confirm or provide rejection reason",
                    )
                    if result:
                        raise NonTerminatingException(f"Command not executed: {result}")

            return super().execute_action(action)

        def has_finished(self, output: dict[str, str]):
            try:
                return super().has_finished(output)
            except Submitted:
                if self.config.confirm_exit:
                    new_task = self.app.input_bar.request_input(
                        "Agent wants to finish. Type a comment for a new task or press Enter to quit.",
                    ).strip()
                    if new_task:
                        raise NonTerminatingException(f"The user added a new task: {new_task}")
                raise

        def run(self, task: str, **kwargs: Any) -> tuple[str, str]:  # type: ignore[override]
            try:
                exit_status, result = super().run(task, **kwargs)
            except Exception as exc:  # pragma: no cover
                self.app.call_from_thread(self.app.on_agent_finished, "ERROR", str(exc))
                self.app.call_from_thread(self.app.action_quit)
                return "ERROR", str(exc)
            else:
                self.app.call_from_thread(self.app.on_agent_finished, exit_status, result)
                self.app.call_from_thread(self.app.action_quit)
                return exit_status, result

    class _LogNotifyHandler(logging.Handler):
        def __init__(self, callback):
            super().__init__()
            self.callback = callback

        def emit(self, record: logging.LogRecord):
            self.callback(record)

    class DockedInputBar(Container):
        def __init__(self) -> None:
            super().__init__(id="input-bar")
            self.can_focus = True

            self._prompt_display = Static("", id="input-prompt")
            self._hint_text = Static("", id="input-hint")
            self._single = Input(placeholder="Type your input...")
            self._multi = TextArea(show_line_numbers=False, id="input-multiline")

            self._multiline_mode = False
            self._pending_prompt: str | None = None

            self._event = threading.Event()
            self._result: str | None = None

        def compose(self) -> Any:
            with Vertical(id="input-stack"):
                yield self._prompt_display
                yield self._hint_text
                yield self._single
                yield self._multi

        @property
        def pending_prompt(self) -> str | None:
            return self._pending_prompt

        def on_mount(self) -> None:
            self._multi.display = False
            self._update_hint()

        def on_focus(self) -> None:
            if self._multiline_mode:
                self._multi.focus()
            else:
                self._single.focus()

        def request_input(self, prompt: str) -> str:
            self._event.clear()
            self._result = None
            self._pending_prompt = prompt
            self._prompt_display.update(prompt)
            self._update_hint()
            self.display = True
            self.on_focus()
            self._event.wait()
            return self._result or ""

        def _complete(self, value: str) -> None:
            self._result = value
            self._pending_prompt = None
            self._single.value = ""
            self._multi.text = ""
            self._multiline_mode = False
            self._multi.display = False
            self._single.display = True
            self._update_hint()
            self._event.set()

        def _update_hint(self) -> None:
            if self._multiline_mode:
                self._hint_text.update("Ctrl+D submit · Tab focus")
            else:
                self._hint_text.update("Enter submit · Ctrl+T multiline · Tab focus")

        def on_input_submitted(self, event: Any) -> None:
            if not self._multiline_mode:
                self._complete(event.value.strip())

        def on_key(self, event: Any) -> None:
            if event.key == "ctrl+t" and not self._multiline_mode:
                event.prevent_default()
                self._multiline_mode = True
                self._multi.text = self._single.value
                self._multi.display = True
                self._single.display = False
                self._update_hint()
                self.on_focus()
                return

            if self._multiline_mode and event.key == "ctrl+d":
                event.prevent_default()
                self._complete(self._multi.text.strip())

    class OpencodeTextualAgent(App):
        BINDINGS = [
            Binding("q,ctrl+q", "quit", "Quit"),
            Binding("y,ctrl+y", "yolo", "YOLO mode"),
            Binding("c", "confirm", "Confirm mode"),
            Binding("u,ctrl+u", "human", "Human mode"),
            Binding("end", "scroll_end", "Scroll bottom", show=False),
            Binding("f1,question_mark", "toggle_help", "Help", show=False),
        ]

        def __init__(self, model: Any, env: Any, **kwargs: Any):
            css_path = os.environ.get(
                "MSWEA_OPENCODE_STYLE_PATH",
                str(Path(__file__).with_suffix(".tcss")),
            )
            self.__class__.CSS = Path(css_path).read_text()

            super().__init__()
            self.agent_state: Literal["UNINITIALIZED", "RUNNING", "AWAITING_INPUT", "STOPPED"] = "UNINITIALIZED"
            self.agent = _OpencodeAgent(self, model=model, env=env, **kwargs)

            self._vscroll = VerticalScroll(id="transcript")
            self._status = Static("", id="status")
            self.input_bar = DockedInputBar()

            self._spinner = Spinner("dots")
            self.exit_status = "ExitStatusUnset"
            self.result = ""

            self._log_handler = _LogNotifyHandler(lambda r: self.call_from_thread(self._on_log, r))
            logging.getLogger().addHandler(self._log_handler)

        @property
        def messages(self) -> list[dict]:
            return self.agent.messages

        @property
        def config(self) -> Any:
            return self.agent.config

        @property
        def env(self) -> Any:
            return self.agent.env

        @property
        def model(self) -> Any:
            return self.agent.model

        def run(self, task: str, **kwargs: Any) -> tuple[str, str]:  # type: ignore[override]
            threading.Thread(target=lambda: self.agent.run(task, **kwargs), daemon=True).start()
            super().run()
            return self.exit_status, self.result

        def compose(self) -> Any:
            yield Header()
            with Container(id="main"):
                with self._vscroll:
                    yield Vertical(id="transcript-content")
            with Container(id="bottom"):
                yield self._status
                yield self.input_bar
            yield Footer()

        def on_mount(self) -> None:
            self.agent_state = "RUNNING"
            self._refresh_transcript()
            self.set_interval(1 / 8, self._update_status)

        def on_unmount(self) -> None:
            logging.getLogger().removeHandler(self._log_handler)

        def on_message_added(self) -> None:
            at_bottom = self._vscroll.scroll_y <= 1
            self._refresh_transcript(auto_follow=at_bottom)

        def on_agent_finished(self, exit_status: str, result: str) -> None:
            self.agent_state = "STOPPED"
            self.exit_status = exit_status
            self.result = result
            self.notify(f"Agent finished: {exit_status}")
            self._refresh_transcript(auto_follow=True)

        def _on_log(self, record: logging.LogRecord) -> None:
            if record.levelno >= logging.WARNING:
                self.notify(f"[{record.levelname}] {record.getMessage()}", severity="warning")

        def _refresh_transcript(self, *, auto_follow: bool = False) -> None:
            container = self.query_one("#transcript-content", Vertical)
            container.remove_children()

            transcript_mod = importlib.import_module("livesweagent.ui.parse.transcript")
            messages_to_transcript = getattr(transcript_mod, "messages_to_transcript")
            transcript = messages_to_transcript(self.agent.messages)

            if not transcript:
                container.mount(Static("Waiting for agent to start..."))
                return

            for item in transcript:
                widget = Static(Text(item.text, no_wrap=False), classes=f"row {item.type}")
                container.mount(widget)

            if self.input_bar.pending_prompt is not None:
                self.agent_state = "AWAITING_INPUT"
            else:
                if self.agent_state != "STOPPED":
                    self.agent_state = "RUNNING"

            self._update_status()
            self.refresh()

            if auto_follow:
                self.action_scroll_end()

        def _update_status(self) -> None:
            status = self.agent_state
            if self.agent_state == "RUNNING":
                spinner_frame = str(self._spinner.render(time.time())).strip()
                status = f"{status} {spinner_frame}"
            mode = getattr(self.agent.config, "mode", "?")
            cost = getattr(self.agent.model, "cost", 0.0)
            self._status.update(f"{status} · mode={mode} · cost=${cost:.2f}")
            self.title = f"swesh - {status}"
            try:
                self.query_one("Header").set_class(self.agent_state == "RUNNING", "running")
            except NoMatches:
                pass

        def get_system_commands(self, screen):
            yield from super().get_system_commands(screen)
            for binding in self.BINDINGS:
                action_method = getattr(self, f"action_{binding.action}")
                yield SystemCommand(binding.description, binding.tooltip, action_method)

        def action_scroll_end(self) -> None:
            self._vscroll.scroll_to(y=0, animate=False)

        def action_yolo(self) -> None:
            self.agent.config.mode = "yolo"
            if self.input_bar.pending_prompt is not None:
                self.input_bar._complete("")
            self.notify("YOLO mode enabled")

        def action_confirm(self) -> None:
            if self.agent.config.mode == "human" and self.input_bar.pending_prompt is not None:
                self.input_bar._complete("")
            self.agent.config.mode = "confirm"
            self.notify("Confirm mode enabled")

        def action_human(self) -> None:
            if self.agent.config.mode == "confirm" and self.input_bar.pending_prompt is not None:
                self.input_bar._complete("User switched to manual mode, this command will be ignored")
            self.agent.config.mode = "human"
            self.notify("Human mode enabled")

    return OpencodeTextualAgent(model, env, **agent_kwargs)
