# Workflow exports

This directory holds the raw n8n workflow JSONs. Each one is the source of record — every diagram and node-by-node walkthrough in [`../docs/workflows/`](../docs/workflows/) is derived from these files.

## Files

| File | Deep-dive |
|---|---|
| `microvest-content-engine.json` | [W1](../docs/workflows/microvest-content-engine.md) |
| `crypto-trend-tweet-generator.json` | [W2](../docs/workflows/crypto-trend-tweet-generator.md) |
| `news-to-twitter-distribution.json` | [W3](../docs/workflows/news-to-twitter-distribution.md) |
| `autonomous-ai-agent-system.json` | [W4](../docs/workflows/autonomous-ai-agent-system.md) |
| `transform-labs-event-promo.json` | [W5](../docs/workflows/transform-labs-event-promo.md) |

## Sanitization

Every JSON in this directory has been sanitized for portfolio publication:

- **Credential references are by ID only.** n8n's credential store keeps the actual tokens server-side; the IDs you see in the JSON are pointers, not secrets.
- **Hardcoded bearer tokens replaced with environment variables.** Where an HTTP node had a literal token in the headers, it's been rewired to read from `$env.OPENAI_API_KEY` / `$env.TWITTER_BEARER_DRIPPY` / `$env.TWITTER_BEARER_DROOPY`. See [`../.env.example`](../.env.example).
- **`pinData` blocks stripped.** n8n stores sample execution data alongside the workflow; that data has been removed to avoid leaking third-party content into the repo.

## Importing

```
n8n → Settings → Workflows → Import from File
```

Import each file. Then attach credentials in the n8n credential manager — see [`../docs/SETUP.md#step-2--create-n8n-credentials`](../docs/SETUP.md#step-2--create-n8n-credentials) for the credential map.

## Sub-workflows

Workflows 2, 4, and 5 reference sub-workflow tools (`toolWorkflow`) by `workflowId`. These sub-workflows are not in this directory; they live in the same n8n instance and are documented at the interface level in each parent workflow's deep-dive. If you import the parents into a fresh n8n instance, you'll need to either also import the sub-workflows or repoint the orchestrator's tool array to your equivalents.
