---
name: task-logger-hooks
description: Install, repair, or extend task-start/task-end logging hooks for Gemini CLI, GitHub Copilot CLI, Codex, and Claude Code, so every completed agent task is appended as one line to a shared TaskLog.md. Use when setting up these hooks on a new machine, fixing a broken hook, or porting the pattern to a new agent.
---

# Task Logger Hooks

## Purpose

Each of Victor's four CLI agents (Gemini CLI, Copilot CLI, Codex, Claude Code)
supports lifecycle hooks. This skill wires each agent's start/end hook pair to
append one markdown line per completed task to a shared log:

```
~/Developer/design/active/TaskLog.md
```

Entry format:

```
- **[Category]** (142s) - 2026-03-07 02:31:43: Implement a hook to track how long it takes...
```

## Shared logic

Every agent follows the same two-phase pattern:

1. **Start hook** — captures the prompt/task text and a start timestamp, keyed
   by session (and turn, for Codex). Written to a temp/state file since the
   end hook runs as a separate process.
2. **End hook** — reads that state back, computes duration, infers a category
   from keywords in the prompt (`Bugfix`, `Testing`, `Documentation`,
   `Investigation`, `Feature`, else `Misc`), truncates the description to 120
   chars, and appends one line to `TaskLog.md`. Creates the log file with a
   `# Task Log` header if it doesn't exist yet.

Prompts matching system/meta patterns (e.g. `you are codex`, `<system`,
`knowledge cutoff:`) are skipped — these are framework-injected prompts, not
real tasks.

Hooks fail open: any error is caught and swallowed so a broken hook never
blocks the agent.

Codex and Claude Code share a `common.js` module with this logic. Gemini and
Copilot inline it in each script (their hook runtimes invoke each hook as a
standalone process without a shared local module resolution path).

## Per-agent wiring

| Agent | Config file | Start hook | End hook | Install dir |
|---|---|---|---|---|
| Gemini CLI | `~/.gemini/settings.json` | `BeforeAgent` | `AfterAgent` | `~/.gemini/hooks/task-logger/` |
| Copilot CLI | `~/.copilot/hooks/hooks.json` | `sessionStart` | `sessionEnd` | `~/.copilot/hooks/task-logger/` |
| Codex | `~/.codex/hooks.json` | `UserPromptSubmit` | `Stop` | `~/.codex/hooks/task-logger/` |
| Claude Code | `~/.claude/settings.json` | `UserPromptSubmit` | `Stop` | `~/.claude/hooks/task-logger/` |

Codex additionally requires `codex_hooks = true` under `[features]` in
`~/.codex/config.toml` — hooks are inert without it.

State keying differs slightly: Gemini and Copilot key state by session only
(Copilot only ever runs one session at a time per state file); Codex keys by
`session_id` + `turn_id` since `Stop` fires per turn; Claude Code keys by
`session_id`.

## Installing on a new machine

For each agent in scope:

1. Copy that agent's scripts from `assets/<agent>/` (everything except the
   `*.snippet.*`/`hooks.json` config file) into its install dir listed above.
   Preserve the executable bit (`chmod +x`).
2. Wire the config:
   - **Gemini, Claude Code**: these share `settings.json` with unrelated
     config (model, permissions, etc.). Read the existing file, merge in the
     `hooks` block from `assets/<agent>/settings.snippet.json` (union with
     any existing `hooks` keys — don't clobber unrelated hooks the user
     already has), and write it back.
   - **Copilot, Codex**: `hooks.json` is a dedicated hooks-only file. Copy
     `assets/<agent>/hooks.json` straight in, unless one already exists — in
     that case merge the same way as above.
   - **Codex only**: also ensure `codex_hooks = true` under `[features]` in
     `~/.codex/config.toml` (`assets/codex/config.snippet.toml`), merging
     rather than overwriting the file.
3. Confirm `~/Developer/design/active/` exists (`mkdir -p` if not) — the log
   file's parent directory must be present before the first task completes.
4. Smoke test by piping a fake event through the start and end script by hand
   (each reads one JSON object from stdin — check the specific agent's script
   for its exact input shape) and confirming a line lands in `TaskLog.md`.

## Porting to a new agent

To add a fifth agent, find its equivalent of "before first turn" / "after
last turn" hook events, then reuse the Codex/Claude Code `common.js` pattern
(copy it in, key state by whatever session identifier that agent's hook
payload provides) rather than writing the category/truncation/skip logic
from scratch a fifth time.

## Reference files

Live, working scripts and config snippets for all four agents are in
`assets/`, one subdirectory per agent. These are the actual deployed files
from Victor's machine — copy them verbatim rather than re-deriving them from
this description.
