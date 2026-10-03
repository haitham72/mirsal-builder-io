# deploy/: the hosted Mirsal, prepared (branch `deployment`)

**Nothing here is switched on.** No Supabase project, no Vercel project, no Render service and no Google OAuth client exist yet; nothing was pushed to any of them. Everything below was written and tested on a PC against fakes,
so that the next session (on another PC) only has to create the accounts and fill in `deploy/env.example`. `docs/deployment_plan.md` is the reasoning, the phases and the open questions; this file is the map of what exists.

```
deploy/
  gateway/        the FastAPI front door (a strangler in front of the unchanged engine server)       tested: mirsal/tests/test_gateway.py (12 tests)
  supabase/       009_accounts, 010_user_analysis, 011_credit_ledger (+ README)                       applied twice and exercised on a scratch Postgres, then dropped
  docker/         Dockerfile (ffmpeg + libvpx-vp9 checked at build time), start.py, compose.yml        start.py smoke-run locally (below)
  render.yaml     the Render blueprint (web + worker), secrets as `sync: false`
  env.example     every variable, with no values
```

and in the engine (`mirsal/mirsal/`), on this branch only:

- `runtime/users.py` + `console/server.py`: the **trusted-gateway login**. With `MIRSAL_GATEWAY_SECRET` (32+ characters) set, a request that carries `X-Mirsal-Gateway-Secret`, comes from loopback and names a well-formed `X-Mirsal-Subject` is that person: a `member` created on first
  sight (`UserStore.ensure_external`). Setting the secret also switches authentication on, so the open sandbox is unreachable on a hosted box. `tests/test_gateway_login.py`.
- `services/telegram.py` + `media/library.py`: **never the same pack twice**. `fingerprint()` (sha256 over the stickers' generator names, the SHA-256 of their bytes and their type; not the pack's name or id), `send(mode="once")` answers from the stored export record
  and calls Telegram not at all; `mode="replace"` and `mode="new_set"` are the two recorded escape hatches (`POST /api/packs/{id}/telegram {mode}`). `tests/test_telegram.py::NeverTwice`.

## How the pieces fit

```
browser --HTTPS--> gateway (deploy/gateway, FastAPI) --loopback--> engine (python -m mirsal serve, the code of this repo, unchanged routes)
                     Host / Origin / CORS-less, Google JWT (Supabase), cookie session, rate limit per person (paid routes stricter), body cap, /healthz /readyz, SSE pass-through
```

The gateway strips everything a client could use to impersonate (`Authorization`, `Cookie`, `Origin`, `Sec-Fetch-*`, any `X-Mirsal-*`) and adds its own identity headers. A person is always a `member`: the owner's screens (library, Telegram setup, user list) are not reachable from the internet.
`python -m mirsal doctor` still works on the engine; the gateway refuses to start without a 32+ character secret and a JWT issuer (`Settings.problems()`).

## What the next session does, in order

1. Read `docs/deployment_plan.md` sections 6, 7 and 17 and answer its nine questions (numbered W40-W48 in `docs/waiting-for-haitham.md`) with Haitham (which host, whose Higgsfield account, one bot or one per person, the IP retention days...).
2. Create the Supabase project, enable the Google provider, apply `deploy/supabase/migrations/009..011` (see `deploy/supabase/README.md`), create the Google OAuth client.
3. Fill `deploy/env.example` into the host's environment (Render dashboard, or `deploy/.env` for `docker compose -f deploy/docker/compose.yml --env-file deploy/.env up -d --build`).
4. Run the engine's `python -m mirsal db migrate` against the Supabase pooler, then `python -m mirsal doctor`.
5. Build what is still only designed: the code that writes `accounts` / `user_analysis` / `credit_ledger`, the front end's sign-in button (it needs `GET /auth/config`, then `supabase-js` `signInWithOAuth({provider: 'google', options: {redirectTo: <origin>/auth/callback}})`),
   `AssetStore` on S3 / Supabase Storage (a worker on another machine cannot see a local `out/`), per-person memory in Postgres, `GET /api/me/export`, `DELETE /api/me`, the retention job. These are deployment_plan.md phases 1, 2, 3 and 5.
6. The scrub runbook (`docs/deployment_plan.md` section 8) before anything is public: rotate first, rewrite second, never the other way round, and only with Haitham's explicit go.

## Verified on the PC that prepared it

- `python -m unittest tests.test_gateway tests.test_gateway_login tests.test_users tests.test_telegram` green (the gateway tests run against the real engine server in-process and a generated RSA key).
- The three SQL files ran twice in a row on a scratch database (dropped afterwards): `reserve_credits` refuses the second of two 6-credit reservations against 10 credits, `settle_credits` twice for one job is refused, a forbidden key in `user_analysis.detail` is refused, `purge_old_ip(30)` nulls the old address.
- `deploy/docker/start.py` run for real on the PC (engine + gateway, a fake Supabase URL): `/healthz` 200, the Studio page 200, `/api/me` without a sign-in 401, `/readyz` 503 because the fake issuer's keys cannot be fetched (the right answer). Two bugs found and fixed by that run: the engine answers 401 to an unidentified health poll once the secret is set, and a `*` argument is glob-expanded by the Windows C runtime.
- NOT verified: the Docker build (Docker was not used here), Render, Supabase Auth with a real project, Google, a real browser.
