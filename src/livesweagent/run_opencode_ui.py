"""Console entrypoint for `mini-opencode`.

Uses lazy imports to keep basic importability in minimal environments.
"""

from __future__ import annotations

import importlib
import os
import traceback
from pathlib import Path
from typing import Any


def main() -> None:
    typer = importlib.import_module("typer")
    litellm = importlib.import_module("litellm")
    yaml = importlib.import_module("yaml")

    HTML = importlist("prompt_toolkit.formatted_text").HTML
    FileHistory = importlist("prompt_toolkit.history").FileHistory
    PromptSession = importlist("prompt_toolkit.shortcuts").PromptSession
    Console = importlist("rich.console").Console

    minisweagent_mod = importlib.import_module("minisweagent")
    config_mod = importlib.import_module("minisweagent.config")
    local_env_mod = importlib.import_module("minisweagent.environments.local")
    models_mod = importlib.import_module("minisweagent.models")
    first_time_mod = importlib.import_module("minisweagent.run.extra.config")
    save_mod = importlib.import_module("minisweagent.run.utils.save")
    log_mod = importlib.import_module("minisweagent.utils.log")

    global_config_dir = getattr(minisweagent_mod, "global_config_dir")
    builtin_config_dir = getattr(config_mod, "builtin_config_dir")
    get_config_path = getattr(config_mod, "get_config_path")
    LocalEnvironment = getattr(local_env_mod, "LocalEnvironment")
    get_model = getattr(models_mod, "get_model")
    configure_if_first_time = getattr(first_time_mod, "configure_if_first_time")
    save_traj = getattr(save_mod, "save_traj")
    logger = getattr(log_mod, "logger")

    litellm.suppress_debug_info = True  # type: ignore[attr-defined]

    DEFAULT_CONFIG = Path(os.getenv("MSWEA_MINI_CONFIG_PATH", builtin_config_dir / "mini.yaml"))
    DEFAULT_OUTPUT = global_config_dir / "last_mini_run.traj.json"

    console = Console(highlight=False)
    prompt_session = PromptSession(history=FileHistory(global_config_dir / "mini_task_history.txt"))

    app = typer.Typer(rich_markup_mode="rich")

    @app.command()
    def run(
        model_name: str | None = typer.Option(None, "-m", "--model", help="Model to use"),
        model_class: str | None = typer.Option(
            None, "--model-class", help="Model class to use", rich_help_panel="Advanced"
        ),
        task: str | None = typer.Option(None, "-t", "--task", help="Task/problem statement", show_default=False),
        yolo: bool = typer.Option(False, "-y", "--yolo", help="Start in yolo mode"),
        cost_limit: float | None = typer.Option(None, "-l", "--cost-limit", help="Cost limit. Set to 0 to disable."),
        config_spec: Path = typer.Option(DEFAULT_CONFIG, "-c", "--config", help="Path to config file"),
        output: Path | None = typer.Option(DEFAULT_OUTPUT, "-o", "--output", help="Output trajectory file"),
        exit_immediately: bool = typer.Option(
            False,
            "--exit-immediately",
            help="Exit immediately when the agent wants to finish",
            rich_help_panel="Advanced",
        ),
    ) -> Any:
        configure_if_first_time()
        config_path = get_config_path(config_spec)
        console.print(f"Loading agent config from [bold green]'{config_path}'[/bold green]")
        config = yaml.safe_load(Path(config_path).read_text())

        if not task:
            console.print("[bold yellow]What do you want to do?")
            task = prompt_session.prompt(
                "",
                multiline=True,
                bottom_toolbar=HTML(
                    "Submit task: <b fg='yellow' bg='black'>Esc+Enter</b> | "
                    "Navigate history: <b fg='yellow' bg='black'>Arrow Up/Down</b> | "
                    "Search history: <b fg='yellow' bg='black'>Ctrl+R</b>"
                ),
            )
            console.print("[bold green]Got that, thanks![/bold green]")

        if yolo:
            config.setdefault("agent", {})["mode"] = "yolo"
        if cost_limit is not None:
            config.setdefault("agent", {})["cost_limit"] = cost_limit
        if exit_immediately:
            config.setdefault("agent", {})["confirm_exit"] = False
        if model_class is not None:
            config.setdefault("model", {})["model_class"] = model_class

        model = get_model(model_name, config.get("model", {}))
        env = LocalEnvironment(**config.get("env", {}))

        ui_mod = importlib.import_module("livesweagent.ui.textual_opencode")
        create_agent = getattr(ui_mod, "create_opencode_textual_agent")
        agent = create_agent(model, env, **config.get("agent", {}))

        exit_status, result, extra_info = None, None, None
        try:
            exit_status, result = agent.run(task)  # type: ignore[arg-type]
        except Exception as exc:  # pragma: no cover
            logger.error(f"Error running agent: {exc}", exc_info=True)
            exit_status, result = type(exc).__name__, str(exc)
            extra_info = {"traceback": traceback.format_exc()}
        finally:
            save_traj(agent, output, exit_status=exit_status, result=result, extra_info=extra_info)  # type: ignore[arg-type]

        return agent

    app()


def importlist(module_path: str):
    return importlib.import_module(module_path)


if __name__ == "__main__":
    main()
