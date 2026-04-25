# Setup

This is the reproduction guide. By the end of it you will have all four workflows imported, credentials wired up, and a smoke test that posts a single throwaway tweet from the test queue.

## Prerequisites

- **n8n ≥ 1.50** (cloud or self-hosted). The AI agent / tool-agent / structured output parser nodes used here require modern n8n.
- **OpenAI API key** with access to `gpt-5-mini`, `gpt-5.1`, `gpt-image-1`, and `text-embedding-3-small`.
- **A LinkedIn developer app** authorized to post on behalf of an organization page. You'll need the org page ID.
- **Twitter/X developer access** sufficient for OAuth2 user context posting on three accounts. Workflow 4's mention monitor additionally needs Bearer token access for `tweets/search/recent`.
- **Supabase project** (Workflow 4 only) with `pgvector` enabled.
- **Redis** instance reachable from your n8n host (Workflow 4 only).
- **CryptoCompare account** (free tier — Workflow 3) and **CoinGecko** (no auth — Workflow 2).
- **Telegram bot** (optional — Workflow 3's dead path).

## Account checklist

Tick these before importing anything; the workflows will not run without them.

- [ ] OpenAI key in hand
- [ ] LinkedIn org page ID (the workflow's hardcoded ID `78748279` is for `/Microvest`; replace with yours)
- [ ] Three X accounts with OAuth2 apps and post permissions
- [ ] Two X Bearer tokens for the mention-monitor accounts (Drippy + Droopy)
- [ ] Supabase project URL + anon key + service role key
- [ ] Redis host/port/password
- [ ] (Optional) Telegram bot token + chat ID

## Step 1 — Import the workflows

```
Settings → Workflows → Import from File
```

Import each JSON in [`workflows/`](../workflows/) one at a time. Order doesn't matter, but the deep-dives reference each file by name:

- `microvest-content-engine.json`
- `crypto-trend-tweet-generator.json`
- `news-to-twitter-distribution.json`
- `autonomous-ai-agent-system.json`

If you also have the four sub-workflows referenced by Workflows 2 and 4 (Trend Monitor, Crypto Analyst, Engagement, Personality, Customer Support, Community Builder, Banter Coordinator, Performance Analysis), import them first. The orchestrators reference them by `workflowId`, so you'll need to repoint the IDs after import.

## Step 2 — Create n8n credentials

Open `Credentials` and create one entry per row in the table below. The IDs in the imported JSONs will fail to resolve until you either (a) recreate credentials with the same names and let n8n match by name, or (b) reassign each credential reference manually in every node that needs it.

| Credential type | Name to use | Used by |
|---|---|---|
| `openAiApi` | `OpenAi account` | W1, W2, W3, W4 |
| `linkedInOAuth2Api` | `LinkedIn account` | W1 |
| `twitterOAuth2Api` | `Microvest X` | W1, W3 |
| `twitterOAuth2Api` | `Drippy_io` | W1, W2, W4 |
| `twitterOAuth2Api` | `Droopyy_io` | W1, W2, W4 |
| `telegramApi` | `Telegram account` | W3 |
| `supabaseApi` | `Supabase account` | W4 |
| `redis` | `Redis account` | W4 |

## Step 3 — Environment variables

Copy [`/.env.example`](../.env.example) into your n8n instance's environment. On n8n cloud, set them under `Settings → Environment variables`. On self-hosted, set them in your container env or `.env`.

```bash
OPENAI_API_KEY=
TWITTER_BEARER_DRIPPY=
TWITTER_BEARER_DROOPY=
SUPABASE_URL=
SUPABASE_ANON_KEY=
SUPABASE_SERVICE_ROLE_KEY=
REDIS_HOST=
REDIS_PORT=6379
REDIS_PASSWORD=
PINECONE_API_KEY=        # optional — referenced but not currently called
PINECONE_INDEX=microvest-ai-memory
PINECONE_NAMESPACE=personality-memories
SERPAPI_KEY=             # only if you want web search beyond OpenAI's tool
```

The Twitter Bearer tokens are read directly by the raw HTTP nodes in Workflow 4's mention pipeline (`Fetch All Mentions Drippy` / `Fetch All Mentions Droopy`). The OAuth2 credentials are used by the standard `n8n-nodes-base.twitter` post nodes. Both must exist.

## Step 4 — Supabase schema (Workflow 4 only)

Workflow 4 expects two tables and one RPC. Run this in the Supabase SQL editor:

```sql
-- Enable pgvector if not already
create extension if not exists vector;

-- Conversation memory: every successful run of W4 writes here, every new run reads similar past entries.
create table conversation_memory (
  id bigserial primary key,
  created_at timestamptz default now(),
  message text not null,
  agent_combination text[],
  personality text,
  tweet_id text,
  message_embedding vector(1536),
  metadata jsonb default '{}'::jsonb
);

-- Knowledge base: longer-form content the agents can ground in. Filled out of band.
create table ai_knowledge_base (
  id bigserial primary key,
  created_at timestamptz default now(),
  content text not null,
  content_embedding vector(1536),
  metadata jsonb default '{}'::jsonb
);

-- Vector similarity index
create index on conversation_memory using ivfflat (message_embedding vector_cosine_ops) with (lists = 100);
create index on ai_knowledge_base using ivfflat (content_embedding vector_cosine_ops) with (lists = 100);

-- Similarity search RPC used by W4
create or replace function match_conversation_memory(
  query_embedding vector(1536),
  match_count int default 10
)
returns table (
  id bigint,
  message text,
  agent_combination text[],
  personality text,
  similarity float
)
language sql stable as $$
  select
    cm.id,
    cm.message,
    cm.agent_combination,
    cm.personality,
    1 - (cm.message_embedding <=> query_embedding) as similarity
  from conversation_memory cm
  where cm.message_embedding is not null
  order by cm.message_embedding <=> query_embedding
  limit match_count;
$$;
```

## Step 5 — LinkedIn org ID (Workflow 1)

Workflow 1's `Create a post` node has the Microvest org ID `78748279` hardcoded as the author URN. Find your own:

```
https://www.linkedin.com/company/<vanity-name>/
```

Inspect the page or use the LinkedIn API to retrieve the org ID, then replace `78748279` in the `Create a post` node's `Person or Organization` field with `urn:li:organization:<your-id>`.

## Smoke test

To validate without spamming live accounts:

1. **Workflow 3 — News-to-X**: Open the workflow, disable the schedule trigger, and click `Execute Workflow` manually. The Twitter post node will execute against `@Microvest` — to test against a throwaway account, swap the credential on the post node before running.
2. **Workflow 1**: Same approach. The most expensive workflow (`gpt-image-1` is ~$0.20/run) — only run after Workflow 3 passes.
3. **Workflow 2**: Manual execution. CoinGecko is unauthenticated so the data fetch is free; failures here are usually rate-limit related (1 req/sec free-tier cap).
4. **Workflow 4**: Use the chat trigger panel in the n8n editor. Send `"hello, what's the market doing"` and verify the master coordinator returns a JSON response with both Drippy and Droopy keys before enabling the post path.

If Workflow 4's chat returns a `COORDINATION_FAILURE`, the master coordinator could not reach one of its sub-workflow tools. Check that all eight sub-workflows are imported and that their workflow IDs match the ones referenced in the master coordinator's `tools` array.

## Operating costs (rough)

Per full run, OpenAI usage only:

| Workflow | LLM tokens | Image gen | Approx. cost/run |
|---|---|---|---|
| W1 — Content Engine | ~15K | 1× `gpt-image-1` high | $0.25 |
| W2 — Trend Tweets | ~8K (orchestrator) + ~12K (sub-tools) | — | $0.06 |
| W3 — News-to-X | ~3K | — | $0.01 |
| W4 — Autonomous System | ~25K (master) + ~30K (sub-tools) + 1 embedding | — | $0.20 |

At current schedules: W1 ~5×/wk + W2 2×/day + W3 3×/day = roughly **$2-4 per week** in LLM costs. W4 is on-demand.

## Troubleshooting

**Master coordinator returns truncated JSON.** Increase the `maxTokens` on the master agent's chat model, or tighten its system prompt to enforce earlier termination of each personality field.

**Twitter posts hit rate limits.** All three accounts share the OAuth2 app's 50-tweet-per-15-min ceiling on free tier. Stagger schedule triggers to avoid burst posting from W1 + W2 in the same minute.

**LinkedIn post fails with "INVALID_AUTHOR".** The org ID in the `Create a post` node doesn't match an org your OAuth2 token has admin access to. Re-auth the LinkedIn credential and verify scope.

**Supabase returns 0 matches forever.** `match_conversation_memory` returns nothing until at least one row exists in `conversation_memory` with a non-null `message_embedding`. The agent will fall back to the no-context branch and start populating the table on its first successful run.
