# Agent Teams — Master Reference

Source: https://code.claude.com/docs/en/agent-teams (fetched 2026-05-09)

Quick reference for orchestrating Claude Code agent teams in this repo. Optimized for use as a runtime reference — section order roughly mirrors a session lifecycle (enable → spawn → control → clean up).

> **Status:** Experimental. Requires Claude Code v2.1.32+. This repo enables it via `.claude/settings.json` → `env.CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS = "1"` (PR #25).

---

## TL;DR

- A **team** = one **lead** session + N **teammate** sessions, each with its own context window, communicating via a shared **task list** and **mailbox**.
- Different from subagents: teammates talk to each other (not just back to the main agent), and you can interact with them directly.
- You start one by asking the lead in natural language — Claude spawns/coordinates.
- Best for: research, parallel review, debugging with competing hypotheses, multi-file/multi-layer features.
- Worst for: sequential work, same-file edits, tight dependencies, simple tasks (token cost scales linearly with teammate count).

---

## Enable

Already enabled at the project level here via `.claude/settings.json`:

```json
{ "env": { "CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1" } }
```

Equivalent: export `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1` in the shell before launching `claude`.

Verify: `claude --version` ≥ `2.1.32`.

---

## Architecture

| Component     | Role                                                                                       |
| :------------ | :----------------------------------------------------------------------------------------- |
| **Team lead** | The originating Claude Code session. Spawns teammates, coordinates work, handles cleanup.  |
| **Teammates** | Independent Claude Code instances, each with its own context window.                       |
| **Task list** | Shared work items. States: `pending`, `in progress`, `completed`. Tasks can have deps.     |
| **Mailbox**   | Direct teammate-to-teammate (and teammate-to-lead) messaging.                              |

**On-disk locations** (managed automatically — do **not** hand-edit):
- Team config: `~/.claude/teams/{team-name}/config.json` (contains `members[]`: name, agent ID, agent type)
- Task list:   `~/.claude/tasks/{team-name}/`

There is **no** project-level team config. A `.claude/teams/teams.json` in the repo is treated as an ordinary file, not config.

---

## Start a team

Just describe the team in natural language to the lead session. The lead spawns teammates and coordinates.

```
I'm designing a CLI tool that helps developers track TODO comments across
their codebase. Create an agent team to explore this from different angles:
one teammate on UX, one on technical architecture, one playing devil's advocate.
```

You can specify count and model:
```
Create a team with 4 teammates to refactor these modules in parallel.
Use Sonnet for each teammate.
```

Claude won't spawn a team without your approval — if it proposes one, confirm first.

---

## Display modes

Two modes, controlled by `teammateMode` in `~/.claude/settings.json`:

| Setting        | Behavior                                                                                  |
| :------------- | :---------------------------------------------------------------------------------------- |
| `"auto"` (default) | Split panes if already in a tmux session, otherwise in-process.                       |
| `"in-process"` | All teammates run in the lead's terminal. Works anywhere.                                 |
| `"tmux"`       | Split panes (auto-picks tmux or iTerm2).                                                  |

```json
{ "teammateMode": "in-process" }
```

One-shot override: `claude --teammate-mode in-process`

**Split panes require** tmux **or** iTerm2 with the [`it2` CLI](https://github.com/mkusaka/it2) (Python API enabled in iTerm2 → Settings → General → Magic). Not supported in VS Code integrated terminal, Windows Terminal, or Ghostty. tmux works best on macOS — `tmux -CC` from iTerm2 is the recommended entrypoint.

---

## Talk to teammates

**In-process mode:**
- `Shift+Down` — cycle through teammates (wraps to lead after the last one)
- Type — message the currently focused teammate
- `Enter` — view that teammate's session
- `Esc` — interrupt their current turn
- `Ctrl+T` — toggle the task list

**Split-pane mode:** click into the teammate's pane.

Tip: name your teammates explicitly in the spawn instruction (e.g. "spawn three teammates named `ux`, `arch`, `devil`") so you can reference them in later prompts.

---

## Reuse subagent definitions

You can spawn a teammate using any existing subagent definition (project, user, plugin, or CLI scope):

```
Spawn a teammate using the security-reviewer agent type to audit the auth module.
```

Behavior when used as a teammate:
- The subagent's `tools` allowlist and `model` are honored.
- The subagent's body is **appended** to the teammate's system prompt (not replacing it).
- Team coordination tools (`SendMessage`, task management) are **always** available regardless of `tools`.
- `skills` and `mcpServers` frontmatter fields are **NOT** applied — teammates load skills/MCP from project + user settings, like a regular session.

This is the recommended way to define reusable teammate roles. There is no separate "teammate definition" format.

---

## Tasks

- States: `pending` → `in progress` → `completed`.
- A `pending` task with unresolved dependencies cannot be claimed.
- Claiming uses **file locking** to prevent races.
- Two assignment patterns:
  - **Lead assigns**: tell the lead which teammate gets which task.
  - **Self-claim**: a teammate finishing a task picks the next unassigned, unblocked task.
- Aim for ~5–6 tasks per teammate (per docs' guidance).

If the lead doesn't break work down enough, prompt: *"split the work into smaller pieces"*.

---

## Plan approval workflow

For risky/complex tasks, require teammates to plan first:

```
Spawn an architect teammate to refactor the authentication module.
Require plan approval before they make any changes.
```

Flow: teammate works in **read-only plan mode** → submits plan to lead → lead approves (teammate exits plan mode and implements) **or** rejects with feedback (teammate revises and resubmits).

The lead approves autonomously. To shape its judgment, give criteria in your prompt: *"only approve plans with test coverage"*, *"reject plans that modify the database schema"*.

---

## Hooks (quality gates)

Three hook events are specific to teams. All three: **exit code 2** = block + send feedback.

| Hook            | Fires when                              | Exit-2 effect                                        |
| :-------------- | :-------------------------------------- | :--------------------------------------------------- |
| `TeammateIdle`  | Teammate is about to go idle.           | Sends feedback and keeps the teammate working.       |
| `TaskCreated`   | A task is being created.                | Prevents creation, sends feedback.                   |
| `TaskCompleted` | A task is being marked complete.        | Prevents completion, sends feedback.                 |

Configured in `settings.json` under `hooks` like any other hook event.

Related events that may also fire in team contexts: `SubagentStart`, `SubagentStop`.

---

## Permissions

- Teammates inherit the lead's permission settings at spawn time.
- If the lead ran with `--dangerously-skip-permissions`, all teammates do too.
- You can change individual teammate modes **after** spawning, but **not** per-teammate at spawn time.
- Teammate permission prompts bubble up to the lead — pre-approve common ops in the lead's permission settings to reduce interruptions.

---

## Context

Each teammate is fresh:
- Loads project context: `CLAUDE.md`, MCP servers, skills (same as a regular session).
- Receives the lead's spawn prompt.
- Does **NOT** inherit the lead's conversation history.

→ Pack task-specific details into the spawn prompt:

```
Spawn a security reviewer teammate with the prompt: "Review the authentication module
at src/auth/ for security vulnerabilities. Focus on token handling, session
management, and input validation. The app uses JWT tokens stored in
httpOnly cookies. Report any issues with severity ratings."
```

---

## Communication

- **Automatic delivery** — messages sent via `SendMessage` arrive without polling.
- **Idle notifications** — teammates auto-notify the lead when they stop.
- **Shared task list** — visible to all agents.
- **Direct messaging** — by teammate name. To broadcast: send one message per recipient.

---

## Shut down / clean up

Graceful single shutdown:
```
Ask the researcher teammate to shut down
```
The teammate can approve or reject with explanation.

End the team:
```
Clean up the team
```
**Always run cleanup from the lead** (teammates should not — their team context may not resolve correctly). Cleanup fails if teammates are still active, so shut them down first.

---

## Limitations (current, experimental)

- **No session resumption with in-process teammates** — `/resume` and `/rewind` don't restore them. After resume, lead may message non-existent teammates → tell it to spawn new ones.
- **Task status can lag** — teammates sometimes fail to mark complete, blocking deps. Manually update status or nudge them.
- **Shutdown can be slow** — finishes in-flight requests/tool calls first.
- **One team at a time** per lead. Clean up before creating another.
- **No nested teams** — teammates can't spawn their own teams.
- **Lead is fixed** — can't promote a teammate or transfer leadership.
- **Permissions set at spawn** — see Permissions above.
- **Split panes** require tmux or iTerm2 (see Display modes).

---

## Best practices

- Start with **3–5 teammates** for most workflows. Start with 3 for ~15 independent tasks.
- Right-size tasks: self-contained units producing a clear deliverable (a function, a test file, a review).
- Avoid file conflicts — give each teammate its own set of files.
- Wait for teammates to finish: if the lead starts implementing instead of delegating, prompt *"Wait for your teammates to complete their tasks before proceeding"*.
- New to teams? Start with **research/review** tasks (clear boundaries, no parallel writes).
- Monitor and steer — don't let a team run unattended for long.

---

## Example prompts (use cases)

**Parallel code review:**
```
Create an agent team to review PR #142. Spawn three reviewers:
- One focused on security implications
- One checking performance impact
- One validating test coverage
Have them each review and report findings.
```

**Competing-hypothesis debugging:**
```
Users report the app exits after one message instead of staying connected.
Spawn 5 agent teammates to investigate different hypotheses. Have them talk to
each other to try to disprove each other's theories, like a scientific
debate. Update the findings doc with whatever consensus emerges.
```

---

## Troubleshooting

| Symptom                                  | Fix                                                                                  |
| :--------------------------------------- | :----------------------------------------------------------------------------------- |
| Teammates not visible (in-process)       | `Shift+Down` to cycle. They may already be running.                                  |
| Task too small for a team                | Single session or subagents. Lead decides; can override by asking explicitly.        |
| Split panes not working                  | `which tmux`; for iTerm2 verify `it2` CLI + Python API enabled.                      |
| Too many permission prompts              | Pre-approve common ops in permission settings before spawning.                       |
| Teammates stop on errors                 | View their output (Shift+Down or click pane); send instructions or spawn replacement.|
| Lead shuts down before work is done      | Tell it to keep going. Also use *"wait for teammates"* prompt to prevent recurrence. |
| Orphaned tmux session                    | `tmux ls` then `tmux kill-session -t <name>`.                                        |

---

## Subagents vs agent teams (decision table)

|                   | Subagents                                        | Agent teams                                         |
| :---------------- | :----------------------------------------------- | :-------------------------------------------------- |
| Context           | Own context; results return to caller            | Own context; fully independent                      |
| Communication     | Report results back to main agent only           | Teammates message each other directly               |
| Coordination      | Main agent manages all work                      | Shared task list with self-coordination             |
| Best for          | Focused tasks where only the result matters      | Complex work needing discussion + collaboration     |
| Token cost        | Lower                                            | Higher (each teammate is a full Claude instance)    |

Use subagents when you want quick focused workers that report back. Use teams when workers need to share findings, challenge each other, and self-coordinate.
