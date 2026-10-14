# Credits and usage (`generation/usage.py`, `out/model_calls.jsonl`)

<sub>Part of [generation.md](../generation.md).</sub>

Every paid or model call is a ledger line (what, model, params, cost, latency, Higgsfield id, output). `usage.summary` rolls it up by model, by kind, by request (job → task → generation)
and per call; `spent_today` feeds the cap. Estimates match the balance exactly (checked: 7.75 estimated, 7.75 spent). `GET /api/higgsfield` gives the live balance (cached 6 s).
