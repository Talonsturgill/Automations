# Workflow 15 — Slack Modal Router

> **What it does for you:** one Slack Interactivity URL serves every modal in your Slack app. Submit a `/casestudy` form, a `/blog-ideas` form, an `/events` form — they all hit one webhook here, get a sub-3-second ack so Slack never shows the user a timeout error, then fan out to per-form handler workflows by `callback_id`.

> **File:** `workflows/transform-labs-slack-modal-router.json` *(JSON to be added)*
> **Trigger:** Webhook — `POST https://transformlabs.app.n8n.cloud/webhook/slack-modal-router` (configured as the single Interactivity Request URL in the Slack app manifest)
> **Per-run cost:** ~$0 (no LLM in this pipeline; one webhook + one JS parse + one HTTP forward)

## Purpose

This is the workflow that makes Transform Labs' multi-modal Slack experience possible. Slack apps allow exactly **one** Interactivity Request URL — every form submission, button click, and modal close goes there. Most teams hit a wall the second time they want a Slack form: do they overload one giant workflow, or shove everything behind a single URL?

W15 answers that with a clean **router pattern**:

1. The Slack Interactivity URL points here
2. The webhook **acknowledges Slack within the 3-second SLA** (place the `Respond to Webhook` node *before* the routing logic — Slack only needs the empty 200; processing can keep going)
3. A `Switch` node reads `view.callback_id` from the Slack payload
4. Each branch forwards the payload to a per-form sub-workflow at its own webhook path

Result: the marketing team can ship a new Slack form whenever they want — they just add a `callback_id` to the modal, add one Switch case here, and point a forwarder at their handler workflow's webhook. The router doesn't care what the form does; it just gets the right payload to the right place fast enough that Slack never times out.

## Architecture

```mermaid
flowchart LR
    subgraph slack["Slack"]
        SU["User submits modal<br/>(/casestudy, /blog-ideas, etc.)"]:::out
        SI["Slack POSTs to single<br/>Interactivity URL"]:::out
    end

    subgraph router["Router (this workflow)"]
        WH["Webhook<br/>POST /slack-modal-router<br/>responseMode: responseNode"]:::trigger
        EX["Extract Callback ID<br/>JS — parses Slack's<br/>application/x-www-form-urlencoded<br/>payload= URL-encoded JSON"]:::core
        ACK["Acknowledge Slack<br/>(empty 200 within 3s)"]:::out
        SW["Switch by callback_id"]:::core
    end

    subgraph forwarders["Per-form forwarders"]
        F1["Forward to Case Study<br/>POST /casestudy-modal-submit"]:::out
        F2["Forward to Blog Ideas<br/>POST /blog-modal-submit"]:::out
        F3["Forward to Events form<br/>(planned)"]:::out
        NOOP["Unknown Modal<br/>(log + drop)"]:::core
    end

    subgraph handlers["Handler workflows (separate)"]
        H1["Case Study Generator<br/>workflow"]:::core
        H2["Blog Ideas Generator<br/>workflow"]:::core
    end

    SU --> SI --> WH --> EX --> ACK --> SW
    SW -- "casestudy_form" --> F1 --> H1
    SW -- "blog_ideas_form" --> F2 --> H2
    SW -- "events_form (planned)" -.-> F3
    SW -- fallback --> NOOP

    classDef trigger fill:#1f2937,color:#fff,stroke:#0ea5e9
    classDef core fill:#7c2d12,color:#fff,stroke:#fb923c
    classDef out fill:#064e3b,color:#fff,stroke:#34d399
```

## Pipeline detail

### Stage 1 — Webhook + payload parse

`Modal Router Webhook` is configured as `responseMode: responseNode` — meaning n8n waits for an explicit `Respond to Webhook` node downstream rather than auto-responding. That's the seam that makes the 3-second ack pattern work (next stage).

`Extract Callback ID` (JS) handles the **Slack-specific payload format**. Slack interactivity events arrive as `application/x-www-form-urlencoded` with a single field named `payload` whose value is URL-encoded JSON — *not* a normal JSON body. The JS code handles both shapes defensively:

```js
const body = $input.first().json.body;

let parsed = {};
if (typeof body === 'string') {
  // application/x-www-form-urlencoded — the normal Slack shape
  const params = new URLSearchParams(body);
  const payloadStr = params.get('payload');
  if (payloadStr) parsed = JSON.parse(payloadStr);
} else if (body.payload) {
  // Already-decoded by an upstream parser
  parsed = typeof body.payload === 'string'
    ? JSON.parse(body.payload)
    : body.payload;
} else {
  parsed = body;
}

const callbackId = parsed.view?.callback_id || '';
return [{ json: { callback_id: callbackId, payload: parsed, raw_body: body } }];
```

After this node, downstream nodes have `$json.callback_id` (the routing key) and `$json.payload` (the full Slack `view.state.values` object with form input).

### Stage 2 — The 3-second ack pattern

`Acknowledge Slack` (Respond to Webhook, `respondWith: text`, empty body) is placed **immediately after the parse, before any routing logic**. Slack's interactivity API requires a response within 3 seconds or the user sees `*This app is not responding*` and the modal hangs. Most teams discover this the hard way the first time they try to wire up a Slack form that calls a slow downstream service (LLM, third-party API, anything taking >2 seconds).

The fix is structural: send the ack *first*, do the work *after*. The `Respond to Webhook` node returns the response to Slack immediately while the workflow continues executing the Switch + forwarders nodes asynchronously from Slack's perspective. Slack sees an instant 200 OK, the user sees the modal close cleanly, and whatever heavy work the handler workflow needs to do can take 30 seconds or 30 minutes — Slack already moved on.

### Stage 3 — Route by `callback_id`

`Route by Callback ID` (Switch node, `fallbackOutput: extra`) reads `$json.callback_id` and routes to a named output:

| `callback_id` | Output | Forwards to |
|---|---|---|
| `casestudy_form` | `Case Study` | `/casestudy-modal-submit` workflow |
| `blog_ideas_form` | `Blog Ideas` | `/blog-modal-submit` workflow |
| *(any other value)* | fallback | `Unknown Modal (Log)` no-op |

The `callback_id` is a Slack convention — every `views.open` call sets one when the modal is rendered. By making it the routing key, every form-handler workflow stays cleanly separated and the router doesn't need to know anything about the form contents.

A sticky note in the workflow flags an **upcoming third route**: an `events_form` for letting the team paste manual event URLs into Slack and have them ingested into the Notion Events DB (probably feeds W10 or W13's destination). When that ships, it's a 30-second change here: add one Switch case + one HTTP forwarder node.

### Stage 4 — Per-form forwarders

Each forwarder is an HTTP Request node that POSTs the full parsed `$json` payload to the handler workflow's own webhook URL on the same n8n instance:

```
POST https://transformlabs.app.n8n.cloud/webhook/casestudy-modal-submit
POST https://transformlabs.app.n8n.cloud/webhook/blog-modal-submit
```

Why two-hop (router → forwarder → handler) instead of calling the handler directly via `executeWorkflow`?

1. **Async semantics.** The Slack ack already went out. The forwarders fire-and-forget — n8n records the HTTP call but doesn't block the router on a slow handler.
2. **Independent error surfaces.** If the handler workflow fails, only that workflow's error pipeline fires. The router's own execution log stays clean.
3. **Webhook-test mode in n8n.** Each handler workflow has its own webhook test URL — easy to test handlers in isolation by hitting their webhook directly with a sample payload, without going through Slack.

## Why this beats a monolithic Slack workflow

The naive alternative is one giant n8n workflow with the webhook as the trigger and a series of `if` blocks for each form's handling logic. That works for one form. By the third form, it's a 200-node spaghetti mess that nobody can debug and nobody can edit safely without breaking the others.

The router pattern keeps each handler **completely decoupled**:
- One workflow per form (case studies, blog ideas, events, whatever comes next)
- One Slack interactivity URL (Slack's hard requirement)
- One small router that does nothing except dispatch

If a handler breaks, only that form is broken. If a new form ships, the existing handlers don't get touched.

## Skills demonstrated

- **Sub-3-second Slack ack pattern.** Slack's interactivity API enforces a 3-second response SLA — miss it and the user sees a timeout error and the modal hangs. The structural fix is to send the empty 200 OK *immediately* (via a `Respond to Webhook` node placed before the routing logic), then keep processing asynchronously. Easy to miss; obvious in hindsight; standard for production Slack apps.
- **One Slack Interactivity URL → many modals.** Slack apps allow exactly one interactivity URL. The router pattern lets you ship N independent form-handler workflows behind one URL, all dispatched by `callback_id`. New form = new Switch case + new forwarder. No coupling between handlers.
- **Slack-specific payload parsing.** Slack interactivity events arrive as `application/x-www-form-urlencoded` with a `payload=` field whose value is URL-encoded JSON, *not* a JSON body. The defensive JS parse handles both shapes (raw string or already-decoded) — common bug source when teams plug their first Slack interactivity URL into n8n.
- **Two-hop dispatch for clean error surfaces.** The router forwards to handler webhooks via HTTP rather than calling them via `executeWorkflow`. Each handler has its own execution log + error pipeline + test webhook URL. Failure in one handler doesn't pollute the router's execution history; testing a handler doesn't require going through Slack.
- **`callback_id` as the routing convention.** Every Slack modal sets one when rendered via `views.open`. Using it as the dispatch key is the cleanest contract — the modal builder picks the name, the router knows nothing about form contents, the handler just trusts the inbound payload shape it's been wired for.
