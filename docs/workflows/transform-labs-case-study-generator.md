# Workflow 20 — Case Study Generator

> **What it does for you:** anyone in the marketing Slack types `/casestudy`, fills out a short modal (paste a workflow JSON + optional metrics + optional context), and 5-7 minutes later a fully-drafted 800-1200 word case study lands in the Notion `AI Case Study Library` with `Status = Needs Review` and a Slack DM back to the submitter. The marketer never opens an LLM playground; the engineering work is one form-fill away.

> **File:** `workflows/transform-labs-case-study-generator.json` *(JSON to be added)*
> **Triggers:** Two Slack webhooks — `/casestudy` slash command + modal-submit
> **Per-run cost:** ~$0.40-$0.80 (one orchestrator + 6 specialists via the W14 sub-workflow tool, then writer + critic + editor + quality gate; mostly Anthropic Claude Sonnet 4.5 with Gemini 3 Flash on the critic)

## Purpose

This is the **user-facing surface** for the case-study pipeline. It pairs with two other workflows in the repo:

- **W14 (Case Study Brief Generator)** — the sub-workflow that runs the 6 parallel specialists (Executive Summary / Challenge / Solution / Technical Highlights / ROI & Results / Key Takeaways) plus a senior-editor orchestrator. W20 calls W14 as a `toolWorkflow`.
- **W15 (Slack Modal Router)** — the one-URL-many-modals dispatcher that owns the `casestudy_form` callback. The slash-command + modal pair in W20 are the consumer side of that router pattern.

W14 produces a *structured brief* (title + section blurbs + tags + qualityScore + dataConfidenceNotes). W20 then takes that brief and runs a **full writer → critic → editor loop with a hallucination detector** to turn it into prose, gated on a 7.5/10 quality threshold, and finally writes the result to Notion as `databasePage` + chunked content blocks.

The defining engineering choice is **the data-confidence object**. The workflow analyzer (a JS code node, not an LLM) parses the pasted workflow JSON and partitions every fact into one of three buckets — `verified` (node count, services, complexity score, patterns detected), `userProvided` (only the metrics the operator typed into the modal), and `needsPlaceholder` (anything else). The brief writer, the case-study writer, the critic, and the editor are all given the same bucket structure in their prompts. The critic's job is then mechanical: any specific dollar amount, percentage, or hour-saving claim that *isn't* in the `userProvided` bucket is a hallucination, full stop. This is what keeps the autonomous-draft pipeline from inventing ROI numbers no one can defend in a sales conversation.

## Architecture

```mermaid
flowchart TB
    subgraph slack_in["Slack Frontend"]
        SC["/casestudy<br/>slash command"]:::trigger
        WHC["Slash Command Webhook"]:::trigger
        PSC["Parse Slash Command"]:::core
        OPM["Open Modal Form<br/>views.open API"]:::out
        ACK1["Ack Slash<br/>(empty 200)"]:::core
        FORM["User fills modal:<br/>workflow JSON + project name<br/>+ industry + metrics + context"]:::core
        WHM["Modal Submit Webhook"]:::trigger
        PMS["Parse Modal Submission"]:::core
        ACK2["Ack &amp; Close Modal<br/>response_action: clear"]:::core
        DM1["Notify Processing Started<br/>(DM submitter)"]:::out
    end

    subgraph analyze["Phase 1 — Intake &amp; Analysis"]
        PREP["Prepare for Workflow Analyzer"]:::core
        ANA["Workflow Analyzer (JS)<br/>node categorization<br/>complexity score<br/>pattern detection<br/>dataConfidence buckets"]:::core
    end

    subgraph brief["Phase 2-3 — Specialists + Orchestrator (calls W14)"]
        BRIEF["Generate Case Study BRIEF<br/>Claude Sonnet 4.5 + Think tool"]:::ai
        TEAM["Brief Writing Team<br/>(W14 sub-workflow tool)"]:::ai
    end

    subgraph write["Phase 4 — Writer / Critic / Editor"]
        WRITE["Write Full Case Study<br/>Claude Sonnet 4.5"]:::ai
        CRIT["Critique Case Study<br/>Gemini 3 Flash<br/>(hallucination detector)"]:::ai
        UPD["Update Case Study<br/>Claude Sonnet 4.5<br/>(em-dash strip + voice fix)"]:::ai
        QC{"Quality Check<br/>score ≥ 7.5?"}:::core
    end

    subgraph publish["Phase 5-6 — Notion + Slack"]
        NOT["Notion: AI Case Study Library<br/>create databasePage<br/>(Status = Needs Review)"]:::data
        BLK["Prepare Blocks<br/>(2000-char paragraph chunks)"]:::core
        APP["Append Content<br/>PATCH /v1/blocks/{id}/children"]:::data
        DM2["Slack DM submitter"]:::out
        CH2["Slack #marketing-linkedin-posts"]:::out
    end

    SC --> WHC --> PSC --> OPM --> ACK1
    OPM -. opens .-> FORM
    FORM --> WHM --> PMS --> ACK2 --> DM1 --> PREP --> ANA --> BRIEF
    TEAM -. ai_tool .-> BRIEF
    BRIEF --> WRITE --> CRIT --> UPD --> QC
    QC -- yes --> NOT --> BLK --> APP --> DM2
    APP --> CH2
    QC -- no, loop back --> CRIT

    classDef trigger fill:#1f2937,color:#fff,stroke:#0ea5e9
    classDef core fill:#7c2d12,color:#fff,stroke:#fb923c
    classDef ai fill:#312e81,color:#fff,stroke:#a78bfa
    classDef data fill:#374151,color:#fff,stroke:#9ca3af
    classDef out fill:#064e3b,color:#fff,stroke:#34d399
```
