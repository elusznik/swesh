# `swesh`

!!! abstract "Overview"

    `swesh` is the swesh-default interactive CLI.

    Compared to upstream `mini` UIs, `swesh` defaults to an **opencode-style Textual TUI**:

    - Continuous, append-only transcript (no step paging)
    - Fixed bottom status + input bar
    - Visible but dim rendering of agent reasoning (`THOUGHT:`)
    - Distinct blocks for tool calls (the ` ```bash ...``` ` action) and tool output/observations

    The goal for now is **flag compatibility** with `mini` (same CLI options, same config resolution), while evolving the UI.

## Command line options

Invocation:

```bash
swesh [options]
```

`swesh` currently supports the same flags as `mini`:

- `-t`/`--task`: Specify a task to run (else you will be prompted)
- `-c`/`--config`: Config file to use (same resolution rules as `mini`)
- `-m`/`--model`: Model name (same as `mini`)
- `--model-class`: Model class override (same as `mini`)
- `-y`/`--yolo`: Start in yolo mode (same as `mini`)
- `-l`/`--cost-limit`: Set cost limit (same as `mini`)
- `-o`/`--output`: Trajectory output file
- `--exit-immediately`: Don’t prompt when agent wants to finish

### `MSWEA_VISUAL_MODE_DEFAULT`

Unlike `mini`, `swesh` defaults to the opencode-style UI.

- `swesh -v` always uses the legacy pager-style UI.
- `MSWEA_VISUAL_MODE_DEFAULT` is not used to flip the UI selection for `swesh`.

### `-v/--visual`

`swesh` uses the opencode-style UI by default.

If you pass `-v/--visual`, it switches to the **legacy pager-style Textual UI** (the same UI you get from `mini -v`).

```bash
swesh -v [other options]
```

## Key bindings (opencode UI)

The opencode-style UI currently reuses the keybinding semantics from `mini -v` where it makes sense:

- `q` / `ctrl+q`: Quit
- `c`: Confirm mode
- `y` / `ctrl+y`: YOLO mode
- `u` / `ctrl+u`: Human mode

Input:

- `Enter`: submit single-line input
- `Ctrl+T`: switch to multi-line input
- `Ctrl+D`: submit multi-line input

## Styling

To override the default opencode UI theme, set:

- `MSWEA_OPENCODE_STYLE_PATH` to a path to a `.tcss` file.

## Saving output

`swesh` saves a trajectory JSON (same format as `mini`). The default output path is:

- `last_swesh_run.traj.json` under the global config directory.

## Implementation notes

- UI design/spec: `docs/advanced/textual_opencode_ui.md`
- Entry point: `src/livesweagent/run_swesh.py`
- Opencode Textual app: `src/livesweagent/ui/textual_opencode.py`

{% include-markdown "../_footer.md" %}
