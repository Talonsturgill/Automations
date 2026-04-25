# LinkedIn + Twitter Automations

A portfolio of workflows running real autonomous content systems across LinkedIn, three Twitter/X accounts, and a branded marketing email channel. Two AI personalities (`Drippy_io`, `Droopyy_io`) and one brand voice (`Microvest`) post on schedule, react to market data, and reply to mentions — without me touching anything. A separate event-promo pipeline turns Columbus AI Meetup events into approval-gated branded emails delivered through Constant Contact.

This repo is the source of record. Every workflow JSON in [`workflows/`](workflows/) is the actual file imported into [`microvest.app.n8n.cloud`](https://microvest.app.n8n.cloud); every diagram in [`docs/`](docs/) is generated from those JSONs.

---

## Workflows

Each workflow is a self-contained system with its own trigger surface, prompt design, and reliability posture. Together they cover the full content footprint — news-driven, market-driven, evergreen, conversational, and event-driven email.

### 1. [Microvest Content Engine](docs/workflows/microvest-content-engine.md)

**News-driven LinkedIn + cross-platform fan-out.** Discovers a trending Bitcoin/AI story via web search, writes a brand-voice LinkedIn post with an AI-generated image, and produces three personality-tuned tweets — one each for Microvest, Drippy, and Droopy — from the same source story. Runs ~5×/week. *7 LLM calls per run.*

### 2. [Crypto Trend Tweet Generator](docs/workflows/crypto-trend-tweet-generator.md)

**Market-data-driven Drippy + Droopy tweets.** Pulls live data from three CoinGecko endpoints, classifies the market state into a trigger type (`opportunity_alert`, `community_love`, `fear_uncertainty`, etc.), and routes to an orchestrator agent that calls four specialized sub-workflow tools to draft both personality tweets. Runs 2×/day. *Hierarchical agent design.*

### 3. [News-to-X Distribution](docs/workflows/news-to-twitter-distribution.md)

**Always-on news pipeline + evergreen humor + Telegram briefing.** A multi-channel canvas. The headline path curates CryptoCompare stories under a strict ranked rubric (breaking → institutional → controversy → BTC-adjacent → surprise) with hard-skip rules for sponsored content, then writes a single high-quality `@Microvest` tweet. Same canvas runs three per-persona evergreen-humor flows and a structured mobile-readable Telegram briefing. Runs 3×/day. *Ranked curation w/ explicit skip rules.*

### 4. [Autonomous AI Agent System](docs/workflows/autonomous-ai-agent-system.md)

**Self-aware multi-agent system with vector memory.** A master coordinator agent that calls eight specialized tool agents, picking which to invoke based on the trigger type. Maintains durable personality state (Big-Five traits + emotional levels) across runs, retrieves the 10 most-similar past conversations from Supabase pgvector to ground the prompt, generates dual-personality output with a Human Imperfection Layer, and posts. Also handles inbound mention replies with influence-weighted prioritization. *The most ambitious single artifact in this repo.*

### 5. [Transform Labs Event Promo](docs/workflows/transform-labs-event-promo.md)

**End-to-end event promotion pipeline with native n8n evals.** Discovers Columbus AI Meetup events from RSS, crawls each page with an Azure OpenAI extractor, drafts a branded email through an Anthropic Claude Sonnet 4.5 strategist + writer-team sub-workflow, gates the draft behind a Notion approval workflow, and publishes approved emails to a Constant Contact list at 9:02 AM daily. Includes a versioned test dataset and eleven quantitative quality metrics for the generated copy. *Multi-LLM, full content lifecycle, production-grade evals.*

### 6. [Transform Labs LinkedIn Carousel Generator](docs/workflows/transform-labs-linkedin-carousel.md)

**Weekly LinkedIn PDF carousel pipeline with a critic-reviser quality gate.** Aggregates AI news from five RSS feeds (TechCrunch, Wired, MIT Tech Review, Ars Technica, OhioX), Gemini 3 Pro picks the single best article for a multi-slide breakdown, Claude Sonnet 4.5 + SerpAPI deep-researches it, distills into 6-8 insights, and writes 8-10 slides plus a LinkedIn caption in the founder's voice. The output then loops through a Gemini critic (six weighted scoring categories, ~50 hard-fail rules, math enforced in the prompt) and a Claude reviser until score ≥9 or six iterations. A 600+ line JS code node renders the slides as branded 3D-gradient HTML, ScreenshotOne converts each one to PNG, Azure Blob hosts the assets, and the assembled carousel lands in Notion Content HQ behind a human approval gate with a Slack notification to `#marketing-linkedin-posts`. Runs Mondays at 8:15 AM. *Cross-vendor judge (Gemini grades Claude), bounded-iteration loop, custom render pipeline, approval gate.*

### 7. [Transform Labs LinkedIn Thought Leadership Engine](docs/workflows/transform-labs-linkedin-thought-leadership.md)

**Weekly LinkedIn thought-leadership post + quote-card generator with voice-impersonation quality gate.** A web-search-grounded Gemini agent generates one quotable insight in the founder's voice, a second Gemini agent does a strictly-bounded research pass (2-3 searches max), and Claude Sonnet 4.5 writes a 500-1000 character post tuned for LinkedIn's "...more" fold (any `\n\n` in the first 250 characters is a hard fail because it triggers premature truncation). The post then loops through a Claude critic (five weighted categories, voice-impersonation as a hard-fail criterion) and a Claude editor until score ≥8.9 or five iterations. The quotable insight is rendered onto a 1080×1080 PNG quote card via the same ScreenshotOne → Azure Blob pipeline as W6, then both land in Notion Content HQ behind a human approval gate. Two-input pipeline: scheduled (Thursdays 8:45 AM) + manual `/thought` Slack command (planned). *Voice impersonation as a quality gate, format-aware writing, shared render pipeline.*

### 8. [Transform Labs Fractional CTO LinkedIn Engine](docs/workflows/transform-labs-fractional-cto-linkedin.md)

**Weekly long-form LinkedIn post targeting C-suite executives at mid-market companies, with outline-first writing and an aggressive AI-tells critique loop.** Pulls from five corporate-and-enterprise RSS feeds (HBR, MIT Sloan Review, McKinsey Insights, Fortune Tech, CIO.com), a Claude News Selector picks the article with the strongest fractional-CTO positioning angle, a dedicated Outline Agent produces a 20-field strategic blueprint (hook strategy, paragraph-by-paragraph structure, key points, tone calibration, target length, quotable insight) before any drafting happens, then Claude Sonnet 4.5 writes a 1800-2500 character post. The post runs through a Claude critic (5-dimension weighted scoring, anti-inflation prompt anchoring, long anti-AI-tells checklist, ~15 hard-fail rules including the `". But"` sentence-start ban and `we`-not-`I` firm-voice rule) and a Claude editor with a 7-item self-check until score ≥8 or five iterations. A 1080×1080 quote-card PNG is rendered before the loop (so the loop never re-renders), then a JS chunker splits the final post into ≤2000-char Notion paragraph blocks for human review. Runs Fridays at 8:45 AM. *Outline-first architecture, anti-AI-tells engineering, anti-inflation scoring, Notion paragraph chunking.*

### 9. [Transform Labs AI Transformation Carousel Engine](docs/workflows/transform-labs-ai-transformation-carousel.md)

**Weekly theme-first 8-slide LinkedIn carousel with rigid slide-role spine.** A Gemini Theme Discovery agent searches the web (max 5 calls) for one contrarian AI-transformation angle, a second Gemini agent does a strictly-bounded research pass (max 3 calls) to find 5-6 mid-market industry examples *with specific metrics*, then Claude Sonnet 4.5 writes a fixed 8-slide carousel: 1 hook + 5 industry-example body slides (each lead with a metric, e.g. `Healthcare + 40% Faster Diagnoses`) + 1 reinforcing-stat slide + 1 CTA. The output runs through a Claude critic-editor loop with REJECT-by-default scoring + ~25 banned phrases + hedging-word ban (`might/could/would/may`) until score ≥9.1 or five iterations. Slides render via an Azure-hosted HTML template with URL-encoded params per slide type — different from W6's inline 600+ line generator. ScreenshotOne → Azure Blob → Notion approval gate → Slack notification. Runs Wednesdays at 8:45 AM. *Theme-first authoring, rigid slide-role spine, templated render, REJECT-by-default critic.*

### 10. [Transform Labs Inbox Event Ingester](docs/workflows/transform-labs-inbox-event-ingester.md)

**Email-in event ingestion that feeds W5.** Polls the marketing inbox every 2 hours via Microsoft Graph, runs every email through a Claude classifier (`is this a real event vs. an OTP, newsletter, receipt, or spam?`), then through a structured `informationExtractor` (7-field schema with explicit fallbacks for every field), then through a two-layer dedup (Graph message ID across executions + normalized event-name match against the existing Notion DB, with all six Unicode dash variants flattened to ASCII so en-dashes don't bypass dedup), then writes survivors into the Notion Events database that W5 reads from. Notifies `#marketing-events` on Slack and emails a confirmation back to internal senders (`@transformlabs.com`) only. *Two-stage LLM pipeline (cheap classifier → expensive extractor), two-layer dedup, Unicode dash normalization, workflow pairing with W5 via shared Notion state.*

---

## System view

```mermaid
flowchart LR
    subgraph triggers["Triggers"]
        S1["Schedule"]
        MENT["X mentions<br/>20-min poll"]
        CHAT["Chat trigger"]
        RSS["RSS poll"]
        WH["Webhook"]
    end

    subgraph sources["Inputs"]
        WEB["OpenAI<br/>web search"]
        CG["CoinGecko"]
        CC["CryptoCompare<br/>news"]
        TW["Twitter API v2"]
        MEET["Meetup RSS"]
        MX["Microsoft Graph<br/>(marketing inbox)"]
    end

    subgraph engines["n8n Workflows"]
        W1["W1 - Content Engine<br/>linear, 7 LLMs"]
        W2["W2 - Trend Tweets<br/>orchestrator + 4 tools"]
        W3["W3 - News-to-X<br/>curator + writer"]
        W4["W4 - Autonomous System<br/>master + 8 tools + memory"]
        W5["W5 - Event Promo<br/>strategist + writer team<br/>+ native evals"]
        W6["W6 - LinkedIn Carousel<br/>writer + critic-reviser loop<br/>+ HTML render pipeline"]
        W7["W7 - Thought Leadership<br/>insight + writer + critic loop<br/>+ quote-card render"]
        W8["W8 - Fractional CTO<br/>selector + outline + writer<br/>+ critique-edit loop"]
        W9["W9 - AI Theme Carousel<br/>theme + research + 8-slide writer<br/>+ critic-editor loop"]
        W10["W10 - Inbox Event Ingester<br/>Graph poll + classifier + extractor<br/>+ two-layer dedup, feeds W5"]
    end

    subgraph memory["State"]
        PG[("Supabase pgvector")]
        RD[("Redis dedup")]
        NOT[("Notion CMS")]
        BLOB[("Azure Blob")]
    end

    subgraph outputs["Outputs"]
        LI["LinkedIn /<br/>Microvest org"]
        TM["X / @Microvest"]
        TD["X / @Drippy_io"]
        TY["X / @Droopyy_io"]
        TG["Telegram briefing"]
        EM["Constant Contact<br/>email list"]
        LC["LinkedIn Carousel /<br/>Transform Labs"]
        LT["LinkedIn Post +<br/>Quote Card /<br/>Transform Labs"]
        LF["LinkedIn Long-Form +<br/>Quote Card /<br/>Transform Labs"]
        LA["LinkedIn AI Theme<br/>Carousel /<br/>Transform Labs"]
    end

    S1 --> WEB
    S1 --> CG
    S1 --> CC
    S1 --> W7
    RSS --> MEET
    RSS --> W6
    RSS --> W8
    WEB --> W1
    CG --> W2
    CC --> W3
    MENT --> W4
    CHAT --> W4
    TW --> W4
    MEET --> W5
    WH --> W5
    W1 --> LI
    W1 --> TM
    W1 --> TD
    W1 --> TY
    W2 --> TD
    W2 --> TY
    W3 --> TM
    W3 --> TG
    W4 <--> PG
    W4 <--> RD
    W4 --> TD
    W4 --> TY
    W5 <--> NOT
    W5 <--> BLOB
    W5 --> EM
    W6 <--> NOT
    W6 <--> BLOB
    W6 --> LC
    W7 <--> NOT
    W7 <--> BLOB
    W7 --> LT
    W8 <--> NOT
    W8 <--> BLOB
    W8 --> LF
    S1 --> W9
    W9 <--> NOT
    W9 <--> BLOB
    W9 --> LA
    S1 --> MX
    MX --> W10
    W10 --> NOT
    W10 -. populates .-> W5
```

Every other diagram in this repo is generated the same way — by walking the n8n JSON's `nodes` and `connections` keys.

---

## What this demonstrates

The bullets below are the engineering choices that shaped the system. Each one is a skill backed by a specific artifact you can open and read.

- **Agentic architecture (hierarchical orchestration).** Workflows 2, 4, and 5 use orchestrator agents that call other workflows as tools (`toolWorkflow`). The master agent in Workflow 4 has eight tool agents — Engagement, Trend Monitor, Customer Support, Data Analyst, Community Builder, Banter Coordinator, Personality, Performance Analysis — and picks which to invoke based on a trigger-type → agent map. *See [`docs/workflows/autonomous-ai-agent-system.md`](docs/workflows/autonomous-ai-agent-system.md).*

- **Production-grade AI evals.** Workflow 5 uses n8n's native evaluation framework with a versioned test dataset and eleven quantitative quality gates (word count, banned-word presence, punctuation compliance, speaker mention, emoji count, ticket-link presence, and more). Every style rule enforced in the prompt is also enforced in the metrics, so prompt drift is caught instead of shipped. *See [`docs/workflows/transform-labs-event-promo.md`](docs/workflows/transform-labs-event-promo.md#stage-4--evaluation-routing).*

- **Critic-reviser loop with bounded iteration and cross-vendor judging.** Workflow 6 runs a Gemini 3 Pro critic against a Claude Sonnet 4.5 writer, scoring six weighted categories with ~50 enumerated hard-fail rules and an explicit math formula the critic must show its work on. A reviser node applies surgical fixes; the loop exits on `score ≥ 9` OR `iteration_count ≥ 6` so worst-case API spend is bounded. The validator node auto-passes on empty critic responses to defend against infinite loops. *See [`docs/workflows/transform-labs-linkedin-carousel.md`](docs/workflows/transform-labs-linkedin-carousel.md#stage-7--critic-reviser-loop).*

- **Custom HTML render + screenshot pipeline.** Workflow 6's slide generator is a 600+ line JS code node that produces a fully-branded design system per slide — four-stop gradient backgrounds, 3D glass panels via `transform: perspective` rotations, radial glow orbs, per-role layouts (hook / insight / cta / brand_close), Plus Jakarta Sans + DM Sans typography, ghost numbers, progress bars. ScreenshotOne renders each HTML slide to a 1080×1350 PNG, Azure Blob hosts the assets, Notion embeds them inline. Workflow 7 reuses the same screenshot pipeline at 1080×1080 for quote cards. *See [`docs/workflows/transform-labs-linkedin-carousel.md`](docs/workflows/transform-labs-linkedin-carousel.md#stage-8--html-slide-generation).*

- **Voice impersonation as a quality gate.** Workflow 7's critic isn't scoring "is this a good LinkedIn post" — it's scoring "would Ryan Frederick's followers recognize this as his writing." The system prompt grounds the critic in worked examples from his actual Medium posts and treats "sounds like it could come from any company" as a hard fail alongside the punctuation and structural rules. The same workflow encodes platform-physics: any `\n\n` in the first 250 characters is a hard fail because LinkedIn's "...more" fold collapses early when it sees a paragraph break. *See [`docs/workflows/transform-labs-linkedin-thought-leadership.md`](docs/workflows/transform-labs-linkedin-thought-leadership.md#stage-5--critic-reviser-loop).*

- **Outline-first writing + anti-AI-tells engineering.** Workflow 8 separates strategy from prose: a dedicated `Outline Agent` produces a 20-field strategic blueprint (hook strategy, 6-paragraph structure, key points, tone calibration, target length, quotable insight) before the writer ever drafts. Both the writer and critic prompts encode an unusually long checklist of patterns that signal LLM-generated content — back-to-back short sentences, the `[Noun] isn't X. It's Y.` pattern, repeated sentence starters, fragment lists, `It means... It requires...` chains, vague `around` connectors. The critic prompt explicitly anchors the 1-10 scoring scale and instructs the model to default to "the draft is flawed," forbidding 10s — the practical answer to "LLM judges grade everything 8/10." *See [`docs/workflows/transform-labs-fractional-cto-linkedin.md`](docs/workflows/transform-labs-fractional-cto-linkedin.md#stage-3--strategic-outline).*

- **Theme-first authoring with rigid slide-role spine.** Workflow 9 picks a *theme* rather than a single article, then researches 5-6 mid-market industry examples to populate a fixed 8-slide spine (`hook → body × 5 → stat → cta`). Every body slide is required to lead with a specific metric (`Healthcare + 40% Faster Diagnoses`); the structure is the brand voice, which is what makes the publication recognizable week to week. Slides render via an Azure-hosted HTML template with URL-encoded params per slide type — different from W6's 600+ line inline render. Tradeoff: less per-slide visual variety, much simpler per-run code paths. *See [`docs/workflows/transform-labs-ai-transformation-carousel.md`](docs/workflows/transform-labs-ai-transformation-carousel.md#stage-4--write).*

- **Two-stage LLM pipeline + paired-workflow composition through shared Notion state.** Workflow 10 polls the marketing inbox every 2 hours, runs a cheap Claude classifier (`is this a real event vs. an OTP, newsletter, receipt, or spam?`) to firewall out the ~95% of emails that aren't events, then runs an `informationExtractor` only on the survivors. Two layers of dedup — Graph message-ID across executions plus normalized event-name match against the Notion DB (with all six Unicode dash variants flattened to ASCII so en-dashes and em-dashes don't bypass the match). The new events land in the same Notion Events database that **W5** reads from — the two workflows are decoupled (different schedules, different code paths) but composed via shared state. *See [`docs/workflows/transform-labs-inbox-event-ingester.md`](docs/workflows/transform-labs-inbox-event-ingester.md#stage-7--notion-side-dedupe).*

- **Multi-vendor LLM strategy.** Anthropic Claude Sonnet 4.5 for the W5 email strategist (less generic marketing copy on this prompt class), Azure OpenAI `gpt-5-mini` for W5 extraction and parsers, OpenAI `gpt-5.1` for W4's master coordinator, OpenAI `gpt-5-mini` for analysis-class agents, OpenAI `gpt-image-1` for LinkedIn images, OpenAI `text-embedding-3-small` for vector memory. Picked per task, not per vendor preference.

- **Prompt engineering with structural differentiation.** Workflow 1 takes one news article and produces three voices — Microvest brand voice (analytical, ~200 chars, no first-person), Drippy (upbeat mascot, ~100 chars, high-school reading level), Droopy (cynical NY attitude, ~100 chars, hashtag-formula closer). Banned emoji set, banned punctuation set, and reading-level targets are enforced in-prompt across all three. *See [`docs/workflows/microvest-content-engine.md`](docs/workflows/microvest-content-engine.md).*

- **Vector memory and RAG.** Workflow 4 embeds incoming chat with `text-embedding-3-small`, retrieves the 10 most-similar past conversations via Supabase's `match_conversation_memory` RPC, surfaces the most-frequent successful agent combinations from those past runs, and feeds all of it into the master coordinator's prompt. After posting, it embeds the result and writes it back. *See [`docs/SETUP.md`](docs/SETUP.md) for the schema.*

- **Defense-in-depth output parsing.** Every LangChain agent runs through a `structuredOutputParser` (with `autoFix` where it makes sense). Workflows 2 and 4 layer a regex fallback for malformed JSON, and Workflow 4 adds a canned-response final fallback. The system either posts something coherent or fails loudly. Nothing silent.

- **Character-design as engineering.** Workflow 4's Human Imperfection Layer modulates typing-speed-simulated post delays, emoji selection, ellipsis style (`...` for Droopy, `…` for Drippy), tweet length by time of day, and a 10% post-edit chance — per personality, per current emotional state. The bots feel like consistent characters across hundreds of runs because the consistency is structurally enforced, not vibes.

- **Human-in-the-loop where it matters.** Workflow 5's emails sit in a Notion `Content HQ` database with `Status = Not Published` until a human checks `Approved = true`. The 9:02 AM publisher only sends approved entries. Autonomous content for low-stakes channels, human review for branded outbound email.

- **Multi-platform reliability.** Every Twitter post node runs with `retryOnFail` and `continueErrorOutput`. A LinkedIn outage never blocks tweets; a Drippy outage never blocks Microvest. Per-platform failures route to a no-op error branch instead of stopping the run. Workflow 5 routes errors to a dedicated `#n8n-workflow-error` Slack channel.

---

## Stack

| Layer | What I use here |
|---|---|
| **Orchestration** | n8n (cloud) — schedule / RSS / webhook / chat / eval triggers, AI agent / tool agent / structured output parser nodes, sub-workflow tool invocation, native evaluation framework |
| **Models** | OpenAI `gpt-5.1` (W4 master coordinator), `gpt-5-mini` (W1-3 analysis), `gpt-image-1` (LinkedIn images), `text-embedding-3-small` (vector memory); Azure OpenAI `gpt-5-mini` (W5 extraction, W6 auxiliary, W7 hashtags); Anthropic Claude Sonnet 4.5 (W5 email strategist; W6 research / distill / write / revise; W7 write / critic / edit; W8 select / outline / write / critique / edit; W9 write / critic / edit; W10 classify + extract); Google Gemini 3 Pro (W6 topic selector + critic; W7 research; W9 theme + research); Google Gemini 3.1 Pro (W7 insight generator) |
| **State + storage** | Supabase Postgres + pgvector (`conversation_memory`, `ai_knowledge_base`, `match_conversation_memory` RPC); Redis (`processed_tweet:*` dedup); Notion (Events DB shared between W10 writer and W5 reader, Content HQ approval workflow with platform-segmented entries); Azure Blob Storage (event images, carousel slide PNGs, thought-leadership + fractional-CTO quote cards) |
| **External APIs** | LinkedIn Marketing API, Twitter/X API v2 (OAuth2 × 3 accounts + Bearer mention search), CoinGecko (3 endpoints), CryptoCompare News API, Telegram Bot API, Microsoft Graph (mail read + mail send on the marketing mailbox), Meetup RSS, AI-news RSS (TechCrunch / Wired / MIT Tech Review / Ars Technica / OhioX), corporate-and-enterprise RSS (HBR / MIT Sloan / McKinsey / Fortune / CIO.com), OpenAI (chat + image + embeddings), Anthropic, Google Gemini, SerpAPI, ScreenshotOne, Constant Contact (OAuth2), Slack (4 channels + slash commands) |
| **Patterns** | Hierarchical agent / tool-agent topology, sub-workflow modularization, outline-first writing, theme-first authoring, rigid slide-role spines, structured output parsing with autoFix, two-stage LLM pipelines (cheap classifier → expensive extractor), two-layer dedup (per-execution + per-domain), Unicode normalization for fuzzy match, vector retrieval + memory writeback, multi-source data fusion, defensive output parsing, native eval datasets + quantitative quality gates, critic-reviser loops with bounded iteration, cross-vendor LLM judging, voice-impersonation quality gates, anti-AI-tells detection, anti-inflation scoring instructions, REJECT-by-default critics, format-aware writing (LinkedIn fold-physics encoding), HTML-to-PNG render pipelines (inline-generated and template-driven), Notion paragraph chunking, paired-workflow composition through shared Notion state, human-in-the-loop approval gates, multi-vendor LLM routing |

---

## Run it

1. n8n instance (cloud or self-hosted, ≥1.50 for the AI agent and evaluation nodes).
2. Import each file in [`workflows/`](workflows/) and attach the credentials listed in [`docs/SETUP.md`](docs/SETUP.md).
3. Copy [`.env.example`](.env.example) to `.env` and fill in.
4. Run the smoke test in [`docs/SETUP.md`](docs/SETUP.md).

---

## Repo layout

```
.
├── README.md                # this file
├── .env.example             # env vars referenced by the workflows
├── workflows/               # raw n8n exports — sanitized, importable
└── docs/
    ├── ARCHITECTURE.md      # cross-workflow system view + design notes
    ├── SETUP.md             # reproduction guide
    └── workflows/           # one deep-dive per workflow
```

---

## Contact

Talon Sturgill — building agentic systems. [GitHub](https://github.com/talonsturgill).
