# Opencode-style Textual UI (design spec)

This document describes a proposed replacement / alternative to the current `mini -v` (“pager-style”) Textual UI.

It targets an “opencode / Claude Code / Codex CLI” feel:

- A single continuous scrollback transcript (append-only)
- A fixed bottom bar containing status + input
- Clear, stable visual semantics for:
  - user input
  - agent output
  - agent reasoning (`THOUGHT:`) shown dim
  - tool calls (the agent’s ` ```bash ... ``` ` action)
  - tool output (the observation added after an action runs)

This spec is intended to be implemented in a *no-conflict* way (new module + new UI entrypoint), preserving the existing `mini -v` UI unchanged.

## Background

### Current `mini -v` behavior

The current Textual UI is implemented in `src/minisweagent/agents/interactive_textual.py`.

Notable behaviors that motivate this redesign:

- **Pager/step paradigm**: messages are grouped into “steps” (`_messages_to_steps()`), and the UI can display only one step at a time.
- **Input is part of the scroll area**: `SmartInputContainer` is mounted inside the `VerticalScroll`.
- **Boxed cards**: every message is wrapped in a `.message-container` with a background fill (`src/minisweagent/config/mini.tcss`).

### Underlying message model

`DefaultAgent` stores a single `messages: list[dict]` stream. Each message is appended via `add_message(role, content, ...)`.

- `role == "system"`: the system prompt
- `role == "user"`:
  - initial task prompt (`instance_template`)
  - tool observations (`action_observation_template`) after every executed action
  - non-terminating and terminating exception strings (also appended as `user` messages)
- `role == "assistant"`: the model output (expected to contain a `THOUGHT:` section + exactly one ` ```bash ...``` ` block)

## Goals

- **Transcript-first UI**: everything appears in a single scrolling log.
- **Docked bottom bar**:
  - always-visible status row
  - always-visible input widget
  - does not “jump” when input appears/disappears
- **Semantic rendering** of agent turns:
  - show reasoning (`THOUGHT:`) *dim* (visible, but de-emphasized)
  - show tool call (the bash code block) as a distinct, copyable block
  - show tool output (observation) as distinct block(s)
- **Robust classification**: degrade gracefully when messages are malformed.
- **No-conflict implementation**:
  - keep `src/minisweagent/agents/interactive_textual.py` intact
  - implement the new UI in new code paths (suggested: `src/livesweagent/`)

## Non-goals

- Rewriting agent control flow or model prompting (UI-only change).
- Replacing `mini` (REPL UI) or altering its keyboard semantics.
- Perfect parsing of arbitrary observation templates across all configs. The UI should be *good enough* for bundled configs and resilient for others.

## Proposed user experience

### Layout

A three-part layout:

1) **Transcript / scrollback** (top, takes all remaining space)
2) **Status bar** (docked bottom, single line)
3) **Input area** (docked bottom, one or more lines)

Suggested Textual hierarchy (conceptual):

- `Header` (optional)
- `VerticalScroll` transcript
- `Container` bottom bar (docked)
  - `Static` status line (mode / cost / spinner / step)
  - `Input` or `TextArea` for command / confirmation text
- `Footer` (optional)

### Interaction model

- The transcript is append-only.
- Auto-follow (scroll-to-bottom) is enabled only when the user is already at the bottom.
- The input widget is always present; it switches context:
  - confirmation prompt for proposed actions
  - “enter command” prompt in human mode
  - “agent wants to finish” prompt

### Recommended key bindings

These should align with existing `mini -v` expectations where possible:

- `c`: confirm mode
- `y`: yolo mode
- `u`: human mode
- `q`: quit
- `f1` / `?`: help

Input submission:

- single-line: `Enter`
- multi-line: `Ctrl+D` to submit
- toggle single/multi-line: `Ctrl+T` (existing behavior)

Transcript navigation:

- `PageUp` / `PageDown`, `Home` / `End` (Textual defaults)
- optionally `j/k` for scroll, matching existing bindings

## Message classification and rendering

### Why classification is possible

Bundled configs (e.g. `src/minisweagent/config/mini.yaml`, `config/livesweagent.yaml`) constrain assistant messages to:

- Exactly one bash code block (action)
- A `THOUGHT:` reasoning section before the code block

This makes it feasible to reliably split each assistant message into:

1) reasoning text (shown dim)
2) tool call bash block (shown as “command”)
3) any trailing assistant text (rare; show as normal assistant output)

### Assistant parsing rules

Given an assistant message `content: str`:

1) Extract the single bash action block using the agent’s `action_regex` equivalent:
   - match ` ```bash\n(.*?)\n``` ` with DOTALL
2) Split the “prefix” (text before the code block) into:
   - if it contains `THOUGHT:`: treat the entire prefix as `assistant_reasoning`
   - else: treat prefix as `assistant_output` (fallback)
3) Tool call:
   - the captured bash content is `tool_call`
4) Suffix (text after the code block):
   - treat as `assistant_output` if non-empty

If multiple code blocks exist (malformed), the UI should:

- render the full message as `assistant_output`
- optionally highlight “format error” styling

### User message parsing rules

Because `DefaultAgent` uses `role="user"` for both human-authored messages *and* observations/errors, we classify “user” messages heuristically:

- **Initial task**: first non-system `role="user"` message is displayed as `user_input` (the task statement).
- **Tool output (observation)**: if content looks like an observation template, display as `tool_output`.
  - heuristics (OR):
    - starts with `Observation:`
    - starts with `<returncode>`
    - contains `<output>` ... `</output>`
    - contains `<warning>` (truncated output case)
- **Agent/user prompts and errors**: otherwise display as `system_or_agent_prompt` (distinct from real user input).
  - example: `LimitsExceeded`, `FormatError`, `ExecutionTimeoutError` strings and confirmations

This is intentionally imperfect but should handle the repo’s shipped templates.

### Transcript item types

Each rendered row/block in the transcript should have a type and stable CSS class:

- `user_input`
- `assistant_output`
- `assistant_reasoning`
- `tool_call`
- `tool_output`
- `notification` (warnings logged via `logging` handler)

## Styling spec (Textual CSS)

The UI should avoid “boxed cards everywhere” and instead look like a terminal transcript.

Recommended styling principles:

- Minimal container backgrounds; rely on subtle borders / left rules.
- Distinct typography for reasoning vs output.
- Preserve whitespace and allow wrapping except for code blocks.

Suggested classes (names are illustrative):

- `.row.user` (user input)
- `.row.assistant` (assistant output)
- `.row.thought` (assistant reasoning, dim)
- `.row.command` (tool call block)
- `.row.observation` (tool output)

Recommended visual treatments:

- `.row.thought`:
  - lower contrast (`color: $text-muted` or similar)
  - optional italic
- `.row.command`:
  - monospace
  - subtle background different from transcript background
  - left accent rule (e.g. `$accent`)
- `.row.observation`:
  - monospace
  - different accent (e.g. `$primary`)

## Implementation approach (no-conflict)

### New modules

To preserve upstream mergeability, implement the new UI in new modules, e.g.:

- `src/livesweagent/ui/textual_opencode.py` (new Textual `App`)
- `src/livesweagent/ui/opencode.tcss` (new stylesheet)

Avoid modifying `src/minisweagent/agents/interactive_textual.py` other than possibly minimal/helpful hooks (if needed, prefer subclassing).

### Wiring / entrypoint

Add a new CLI switch rather than changing `-v` semantics.

Suggested choices:

- `mini --ui opencode` (string enum)
- or `mini --visual-opencode` (boolean)

`-v/--visual` should keep launching the existing pager UI for backward compatibility.

### State displayed in the status bar

Recommended fields:

- agent state: `RUNNING`, `AWAITING_INPUT`, `STOPPED`
- current mode: `confirm` / `yolo` / `human`
- model cost: `${cost:.2f}`
- spinner animation while running

## Open questions

- Should we display the raw `system` prompt in the transcript, or hide it by default?
- Should we offer a “copy last command” binding?
- Do we want a toggle to collapse/expand `assistant_reasoning`?
