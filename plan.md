# Plan: to the finish line (v1.0)

What the next session does, in order. A step is removed from this file when it is done (its architecture goes into its area doc and `README.md`); when the last step is done this file is deleted. Haitham, 2026-10-04: "finalize the app completely … go to the finish line".

**Definition of finished:** colleagues in the office sign in on the LAN (HTTPS) with an `@nadi.ae` account Haitham approved (dashboard or Telegram), make stickers and particles in the Studio and the chat with their own 10 credits, share packs in a Trending gallery others can like, comment on and use, the chat streams its steps, every failure or report becomes a ticket, and the repository is tagged `v1.0` with docs that describe only what exists.

Each step: one commit (or one per sub-step), its doc updated in the same commit, the tests it earns under the test budget (`docs/testing.md`), pushed.

## 1. Trending (office_lan_plan.md §2.7)

Shared packs in a Library tab, Higgsfield-style: like, comment, ordered by trending / new / most liked; **Use in my workflow** copies a shared pack into your own library for the Studio.

## 2. Finish

`docs/` describes only what exists (no plan files left except the paused `deployment_plan.md` and `burst_plan.md` waiting for W27; this file and `office_lan_plan.md` are deleted); `README.md` is the index of the finished app; the trackers hold only what is still open; tag `v1.0` and push.

## Decisions this plan relies on

HTTPS on the LAN (`serve --lan` uses TLS); private work per person plus the Trending gallery for shared packs (Haitham, 2026-10-04).
