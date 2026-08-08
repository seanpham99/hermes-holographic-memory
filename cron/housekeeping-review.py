#!/usr/bin/env python
"""Housekeeping review of holographic memory_store.db (run as cron job).

Uses the bundled MemoryStore API (same code path as fact_store tool):
  - remove_fact(fact_id) for stale/junk/superseded facts
  - clean() for deterministic junk removal + VACUUM
Works against $HERMES_HOME/memory_store.db while the gateway holds its own
connection (WAL mode allows concurrent access).
"""
import sys

sys.path.insert(0, "/home/sonpham/.hermes/hermes-agent")

from plugins.memory import load_memory_provider

p = load_memory_provider("hrr_memory")
p.initialize(session_id="cron-housekeeping-review")
store = p._store

# (fact_id, reason) — each verified against the DB dump before this run.
# NOTE 2026-07-31: initial run removed 151 facts + updated 31; the lists
# below were then edited to the remaining gaps found in verification
# passes 2-3 (facts 19, 72, 104, 160, 168, 235, 253, 254). Future runs:
# remove_fact returns False for already-removed ids — harmless.
REMOVE = [
    # --- Session-log / ephemeral auto_capture facts (PR micro-status, test
    #     counts, commit hashes, single-moment observations). Stale within
    #     hours; duplicated in git history and past sessions.
    (82, "auto_capture session log: 'Repository: NousResearch/hermes-agent' (dup of 99/104/110/127)"),
    (84, "auto_capture session log: branch force-pushed & merged into main (superseded; PR state is in git)"),
    (85, "auto_capture session log: branch fixes PR #73210 (superseded)"),
    (86, "auto_capture session log: review feedback addressed (ephemeral)"),
    (88, "auto_capture session log: pytest asyncio strict mode (ephemeral; dup of 202)"),
    (89, "auto_capture session log: 'Repo: NousResearch/hermes-agent' (dup of 82/99/104/110)"),
    (90, "auto_capture session log: PR #73210 5 commits, 12/12 tests (ephemeral status)"),
    (91, "auto_capture session log: PR #74020 fix pushed, awaiting re-review (ephemeral)"),
    (92, "auto_capture session log: PR #74020 merged to local main (superseded)"),
    (93, "auto_capture session log: PR #74900 fixed three issues (stale implementation detail)"),
    (94, "auto_capture session log: three branches merged into son/dev (ephemeral)"),
    (95, "auto_capture session log: force-push after review (ephemeral)"),
    (96, "auto_capture session log: merge conflict resolution (ephemeral)"),
    (97, "auto_capture session log: test assertions added (stale implementation detail)"),
    (98, "auto_capture session log: review addressed in commit (ephemeral)"),
    (99, "auto_capture session log: remote/upstream listing (dup of 104/110/127/128)"),
    (100, "auto_capture session log: repo path (dup of 123/139/169/191/203/232)"),
    (101, "auto_capture session log: handler delegation detail (stale; superseded by 192-214 group)"),
    (102, "auto_capture session log: gateway handler detail (stale implementation detail)"),
    (103, "auto_capture session log: provider class location (stale implementation detail)"),
    (105, "auto_capture session log: son/dev merged upstream (dup of 115; ephemeral)"),
    (106, "auto_capture session log: 52 commits ahead (ephemeral)"),
    (107, "auto_capture session log: three PRs exist (dup of 112/129)"),
    (108, "auto_capture session log: GitHub auth account (dup of 113/205)"),
    (109, "auto_capture session log: pre-existing test error (dup of 120)"),
    (110, "auto_capture session log: repo/fork/upstream (dup of 99/104/127/128)"),
    (111, "auto_capture session log: son/dev vs main roles (ephemeral)"),
    (112, "auto_capture session log: 3 PRs open (dup of 107/129)"),
    (113, "auto_capture session log: gh auth switch first (dup of 6/205)"),
    (114, "auto_capture session log: upstream released v0.19.1 (ephemeral; superseded by later releases)"),
    (115, "auto_capture session log: son/dev merged upstream, pushed (dup of 105)"),
    (116, "auto_capture session log: main merged upstream (ephemeral)"),
    (117, "auto_capture session log: before-fix commit counts (ephemeral)"),
    (118, "auto_capture session log: update script fails on diverged main (ephemeral analysis)"),
    (119, "auto_capture session log: full test suite 521 passed (ephemeral)"),
    (120, "auto_capture session log: acp test import error (dup of 109; ephemeral)"),
    (121, "auto_capture session log: ruff PLW1514 note (ephemeral)"),
    (122, "auto_capture session log: setuptools/starlette pins (ephemeral)"),
    (123, "auto_capture session log: project root (dup of 100/139/169/191/203/232)"),
    (124, "auto_capture session log: working tree clean (ephemeral)"),
    (127, "auto_capture session log: user contributes via fork (dup of 99/104/110/128)"),
    (128, "auto_capture session log: git remotes (dup of 104/110)"),
    (129, "auto_capture session log: 3 open PRs (dup of 107/112)"),
    (130, "auto_capture session log: PR branches (dup of 215)"),
    (131, "auto_capture session log: rebased + force-pushed (ephemeral)"),
    (132, "auto_capture session log: preferred workflow (dup of 125; superseded by 133)"),
    (133, "auto_capture session log: cron job details (dup of 126/235; superseded by 235)"),
    (134, "auto_capture session log: cron script path (dup of 126)"),
    (135, "auto_capture session log: cron only syncs git (dup of 125/126)"),
    (136, "auto_capture session log: hermes update risk note (dup of 125/126)"),
    (137, "auto_capture session log: cron can't run inside Hermes (dup of 125/126)"),
    (138, "auto_capture session log: earlier cron removed (ephemeral)"),
    (139, "auto_capture session log: install path (dup of 100/123/169/191/203/232)"),
    (140, "auto_capture session log: update flow detail (dup of 125/126)"),
    (141, "auto_capture session log: fork main commit counts (ephemeral)"),
    (142, "auto_capture session log: meta note about fact ids (self-referential; not a fact)"),
    (143, "auto_capture session log: github username (dup of 83)"),
    (144, "auto_capture session log: TUI feature CLI-only (dup of 153; superseded)"),
    (145, "auto_capture session log: tests located (ephemeral)"),
    (146, "auto_capture session log: /mem tree subprocess (dup of 181/183; superseded)"),
    (148, "auto_capture session log: daily sync cron created (dup of 125/126)"),
    (149, "auto_capture session log: user needs to run /mem (ephemeral)"),
    (150, "user_pref: raw user chat captured as fact ('Please help me do that...') — not a fact"),
    (151, "user_pref: raw user chat captured as fact ('Good! I am clear...') — not a fact"),
    (152, "user_pref: raw user chat captured as fact ('So with the resolve conflict...') — not a fact"),
    (153, "auto_capture session log: /mem exists on son/dev not main (superseded; renamed to /holographic-memory in 192)"),
    (154, "auto_capture session log: feature commit (superseded by 192-214 group)"),
    (155, "auto_capture session log: /mem prefix-match error (superseded; command renamed)"),
    (156, "auto_capture session log: command registration detail (superseded by 192-214 group)"),
    (157, "auto_capture session log: CLI handler location (superseded by 192-214 group)"),
    (158, "auto_capture session log: gateway handler location (superseded by 192-214 group)"),
    (159, "auto_capture session log: tree script location (dup of 214)"),
    (161, "auto_capture session log: 2x/day preference (ephemeral; duplicated in 225/235)"),
    (162, "auto_capture session log: fork name (dup of 104/110/127)"),
    (163, "auto_capture session log: son/dev PR open (dup of 107/112/129)"),
    (164, "auto_capture session log: cron touches only main (dup of 125/126)"),
    (165, "auto_capture session log: rebase workflow (dup of 125/131)"),
    (166, "auto_capture session log: user timezone +07 (ephemeral)"),
    (170, "auto_capture session log: MCP connect logic internals (ephemeral implementation detail)"),
    (171, "auto_capture session log: background MCP discovery location (ephemeral implementation detail)"),
    (172, "auto_capture session log: tavily MCP server command (ephemeral; superseded by 175/176)"),
    (173, "auto_capture session log: hermes mcp configure interactive-only (ephemeral tool note)"),
    (174, "auto_capture session log: SSH password auth enabled (actionable; but ephemeral status note)"),
    (176, "auto_capture session log: GitHub/Slack MCP run details (ephemeral; superseded by 175)"),
    (177, "auto_capture session log: voltagent source path (ephemeral)"),
    (178, "auto_capture session log: error signature (ephemeral; root cause in 167)"),
    (179, "auto_capture session log: worker-limit coincidence (ephemeral)"),
    (180, "auto_capture session log: slash command duplicate registration (ephemeral)"),
    (182, "auto_capture session log: user steering note (dup of 201)"),
    (184, "auto_capture session log: modified files (ephemeral)"),
    (185, "auto_capture session log: env/pty verification (ephemeral)"),
    (186, "auto_capture session log: 21 tests passed (dup of 219; ephemeral)"),
    (187, "auto_capture session log: memory tree shape 94 facts (ephemeral count)"),
    (188, "auto_capture session log: preference recorded (self-referential; dup of 30)"),
    (189, "auto_capture session log: tax fact restated (dup of 64-68)"),
    (190, "user_pref: raw MCP reload notice + user chat captured as fact — not a fact"),
    (191, "auto_capture session log: project root (dup of 100/123/139/169/203/232)"),
    (193, "auto_capture session log: TUI Ink-based detail (ephemeral implementation detail)"),
    (194, "auto_capture session log: ANSI root cause (stale; fixed in 195)"),
    (196, "auto_capture session log: test updated (ephemeral)"),
    (197, "auto_capture session log: gateway restart required (ephemeral)"),
    (198, "auto_capture session log: strip_ansi utility (ephemeral implementation detail)"),
    (199, "auto_capture session log: 103 facts count (ephemeral)"),
    (200, "auto_capture session log: meta note pointing at fact 181 (self-referential)"),
    (201, "auto_capture session log: user steering (dup of 182)"),
    (202, "auto_capture session log: pytest runner (dup of 88; ephemeral)"),
    (203, "auto_capture session log: project root (dup of 100/123/139/169/191/232)"),
    (204, "auto_capture session log: git remote (dup of 104/110/128)"),
    (206, "auto_capture session log: plugin location (dup of 205-group; self-referential)"),
    (207, "auto_capture session log: fact store actions list (self-referential; code, not fact)"),
    (208, "auto_capture session log: probe semantics (self-referential; code doc)"),
    (209, "auto_capture session log: search semantics (self-referential; code doc)"),
    (210, "auto_capture session log: probe fix detail (self-referential; code doc)"),
    (211, "auto_capture session log: numpy availability (ephemeral env check)"),
    (212, "auto_capture session log: ANSI stripping (dup of 195)"),
    (213, "auto_capture session log: /mem renamed (dup of 192)"),
    (214, "auto_capture session log: tree viewer one-shot (dup of 183)"),
    (215, "auto_capture session log: PR #74900 status (dup of 73; superseded by 246)"),
    (216, "auto_capture session log: commit pushed (ephemeral)"),
    (217, "auto_capture session log: commit pushed to son/dev (ephemeral)"),
    (218, "auto_capture session log: son/dev ahead (ephemeral)"),
    (219, "auto_capture session log: 21 tests (dup of 186; superseded by 238)"),
    (220, "auto_capture session log: 'No cleanup action exists' (CONTRADICTS 233; stale)"),
    (221, "auto_capture session log: user requested clean feature (ephemeral planning note)"),
    (222, "auto_capture session log: curator exists (ephemeral)"),
    (223, "auto_capture session log: env date (ephemeral)"),
    (224, "auto_capture session log: ~103 facts (dup of 199; ephemeral)"),
    (226, "auto_capture session log: AI cleanup cadence (dup of 225/228; ephemeral)"),
    (227, "auto_capture session log: decision to build clean (superseded by 233 — shipped)"),
    (228, "auto_capture session log: decision to keep both (dup of 225; ephemeral)"),
    (229, "auto_capture session log: plan steps (superseded by 233 — shipped)"),
    (230, "auto_capture session log: manual review note (ephemeral)"),
    (231, "auto_capture session log: timezone +07 (dup of 166; ephemeral)"),
    (232, "auto_capture session log: project root (dup of 100/123/139/169/191/203)"),
    (234, "auto_capture session log: junk criteria (self-referential; code doc)"),
    (236, "auto_capture session log: retrieval stack (self-referential; code doc)"),
    (237, "auto_capture session log: SBERT considered (ephemeral research note)"),
    (238, "auto_capture session log: 25 tests passed (ephemeral)"),
    (239, "auto_capture session log: commit list (ephemeral)"),
    (240, "auto_capture session log: edit tool guard (ephemeral)"),
    (241, "auto_capture session log: user preference dedup removed (ephemeral)"),
    (242, "auto_capture session log: auto-capture 100-1000 facts (ephemeral)"),
    (243, "auto_capture session log: semantic dedup design (ephemeral planning)"),
    (244, "auto_capture session log: user direction research first (ephemeral planning)"),
    (245, "auto_capture session log: AGENTS.md closed providers (ephemeral research note)"),
    (246, "auto_capture session log: PR #74900 OPEN not merged (ephemeral; dup of 75)"),
    (248, "auto_capture session log: hindsight uses sentence_transformers (ephemeral research)"),
    (249, "auto_capture session log: mem0 external embedders (ephemeral research)"),
    (250, "auto_capture session log: no semantic dedup gate (ephemeral research)"),
    (251, "auto_capture session log: HRR backend (self-referential; code doc)"),
    (252, "auto_capture session log: decision on branch strategy (ephemeral planning)"),
    # --- Pass 2/3 survivors found in verification (kept in list for idempotence) ---
    (19, "dup of 175 after merge (MCP tool list)"),
    (72, "raw fulfilled user request captured as fact ('I love how the claude-mem library...')"),
    (104, "dup of 125 (origin/upstream repo)"),
    (160, "change-log dup of 225 (cron schedule change)"),
    (168, "dup of 167 (tavily verification path, merged into 167)"),
    (235, "dup of 225 (housekeeping cron)"),
    (253, "junk: category 'test', tags 'entity:cron', content dups 125 (auto_capture artifact)"),
    (254, "junk: category 'test', tags 'entity:cron', content dups 125 (auto_capture artifact)"),
]

# Consolidations: superseded facts updated in place with the canonical,
# current statement, so search/probe keep returning the surviving fact.
# (fact_id, new_content, new_tags, reason)
UPDATE = [
    (2, "roofdata host: Node v16.20.2 at /opt/alt/alt-nodejs16/root/usr/bin/node — not on default PATH.", "roofdata,cpanel,host", "trim verbosity; keep the durable fact"),
    (3, "roofdata host: forever needs local prefix install — `npm config set prefix ~/.npm-global && npm install -g forever` (system prefix unwritable).", "roofdata,cpanel,host,forever", "trim; keep durable"),
    (6, "gh CLI locally flips to sonpham-vnham between sessions — run `gh auth switch --user seanpham99` before push/PR/merge.", "roofdata,tooling,gh", "merge dup 113/205 content (auth account + switch command) into one"),
    (12, "Tavily MCP configured (npx mcp-remote bridge): tools tavily_search, tavily_extract, tavily_crawl, tavily_map, tavily_research. Prefer MCP tools over tvly CLI.", "tavily,mcp,config", "keep; add tag"),
    (18, "9Router at http://100.94.122.69:20128/v1; uv for Python tools (PEP 668).", "9router,uv,config", "trim"),
    (38, "User wants holographic fact_store to auto-surface without manual ask; agent must proactively probe fact_store (no system-level injection mechanism yet).", "holographic,memory,user-preference", "keep; restate"),
    (42, "PTG project: 2 repos — ptg-content-generator (cloned ~/Works/, Express+React19+BullMQ+Supabase+Hygraph) + admin dashboard (scrape/process/CMS upload, repo URL unknown, not cloned).", "ptg,repos,architecture", "trim"),
    (45, "PTG Slack #ptg-content-sprint is mostly bot noise (GitHub/Jira notifications); human chat only Jun 26 kickoff. Real conversations in MPDMs (created Jul 29).", "ptg,slack,channels", "trim"),
    (46, "PTG Jira: 50 tickets, 8 open; Sean's tickets (PTG-231/232/233/181) misassigned — needs reassign before working. Key open: PTG-241 (reseed bug), PTG-240 (missing data), PTG-231 (preflight).", "ptg,jira,tickets,backlog", "trim"),
    (47, "PTG team: Brad (CEO), Inga (UX lead), Khang Vuong (dev), Luca/Harshit/Yuri (engineering); Javier mentioned in n8n context — unknown role.", "ptg,team,people", "trim"),
    (48, "PTG focus: client portal (multitenant, Azure-hosted pending), UAT v7, Brad driving product spec; Inga owns UX. ContentGen v6 shipped. Next: PTG-231 preflight fix, n8n/reseed confusion, AWS infra audit.", "ptg,roadmap,architecture", "trim"),
    (58, "PTG repo has Terraform IaC under infra/: live ECS Fargate stack for AWS account 380592536042 in us-east-1 (ALB, ECS services, IAM, logs, SSM, network). infra/README: migration complete 2026-06-27, Railway/App Runner decommissioned. Code still documents single-AZ task placement.", "ptg,terraform,iac,aws,ecs,infra", "trim"),
    (59, "Created GitHub issue decolua/9router#2915: 'Headroom CCR markers injected into tool outputs when lossless mode not set' — root cause: Headroom SmartCrusher CCR injection in 9Router combo pipeline; fix: --lossless flag. Requested docs update, default lossless, config option.", "9router,headroom,ccr,github-issue", "trim"),
    (70, "OpenCode 1.18.9 custom-provider quirk: `api: openai` + `baseURL` for 9Router errors with `\"openai/chat/completions\" cannot be parsed as a URL` on `opencode run -m <provider>/<model>`. Use `npm: @ai-sdk/openai-compatible` + `options.baseURL` (still needs a real API key for /v1/chat/completions). Verified 2026-07-30.", "opencode,9router,custom-provider,bug,openai-compatible", "trim"),
    (71, "9Router auth quirk (localhost:20128): Bearer key from Hermes config works on /v1/models but is rejected `Invalid API key` on /v1/chat/completions. /models success is NOT sufficient proof of completions auth.", "9router,auth,models,chat-completions", "trim"),
    (75, "PRs by seanpham99 on NousResearch/hermes-agent: #73210 (gateway fix), #74020 (auto-capture), #74900 (TUI visualizer). #74891 closed as duplicate of #74900.", "pr,hermes-agent,nousresearch,seanpham99,inventory", "keep; canonical PR inventory (drops OPEN status — stale-prone)"),
    (77, "vnstock skill at ~/.hermes/skills/quant/vnstock/SKILL.md; deps vnstock==4.0.5, dnse-sdk-openapi==1.4.6, msgpack. Use NEW modular API (vnstock.api.quote.Quote, vnstock.api.market.Market, vnstock.api.finance.Finance) — old Vnstock().stock() deprecated.", "vnstock,skill,quant,finance", "trim"),
    (79, "PR #74020 pyproject fix: removed duplicate [dependency-groups.dev]; merged PR deps into [project.optional-dependencies.dev]; squashed to 1 commit (a704635), force-pushed. 7-file diff.", "pr,pyproject,uv,dependency-groups", "trim"),
    (125, "Hermes fork workflow: origin=seanpham99/hermes-agent, upstream=NousResearch/hermes-agent. Daily cron 'hermes-daily-sync' (3 AM) fetches upstream/main, fast-forwards local main, pushes to origin; does NOT run `hermes update` (deps/build/migrations — manual when starting a session). PR branches (feat/*, fix/*) branch off main, rebase onto upstream/main before push --force-with-lease.", "git,workflow,cron,hermes,upstream,fork", "canonical workflow (merges 132/135/136/137/140/164/165)"),
    (126, "Hermes daily sync cron: job_id=31def2a67be1, script=~/.hermes/scripts/hermes-daily-update.sh, schedule='0 3 * * *'. Logic: fetch upstream main; if main..upstream/main > 0 → merge --ff-only; push origin main. Log: ~/.hermes/logs/hermes-update.log.", "cron,daily-sync,script,hermes,maintenance", "canonical cron detail (merges 134/148)"),
    (167, "Tavily MCP 'failed' status fixed: root cause `connect_timeout: 20` too short under parallel npx spawn of 9 servers at startup → asyncio.CancelledError in asyncio.wait_for; bumped to 60 in config.yaml. Verify with `hermes mcp test tavily` (passes standalone ~7.3s).", "tavily,mcp,timeout,fix", "merge 168 (verification path) into root-cause fact"),
    (169, "Hermes install on this box: home /home/sonpham/.hermes/, agent code /home/sonpham/.hermes/hermes-agent/, logs /home/sonpham/.hermes/logs/errors.log.", "hermes,install,paths", "keep; canonical install-path fact"),
    (175, "Configured MCP servers: atlassian-sooperset, chrome-devtools, context7, deepwiki, github, notebooklm, slack, tavily, voltagent.", "mcp,servers,config", "canonical MCP inventory (merges 172/176)"),
    (181, "/mem tree hang root cause: prompt_toolkit leaves tty in raw mode; child subprocess inherits it; Enter sends `\\r` not `\\n`; `input()` blocks waiting for `\\n`.", "holographic,tui,pty,raw-mode", "keep; durable root cause"),
    (183, "Decision: /mem tree (now /holographic-memory tree) is one-shot non-interactive — renders full tree once, exits, no input loop.", "holographic,tui,decision", "merge 214 into canonical"),
    (192, "Slash command /mem renamed to /holographic-memory; aliases /holographic-mem tree|list work; 21 tests pass.", "holographic,tui,slash-command", "keep; canonical command name (merges 213)"),
    (195, "Fix: removed force_terminal=True from _render_facts_table; Rich auto-detects TTY (ANSI) vs non-TTY (plain text).", "holographic,ansi,rich", "keep; canonical ANSI fix (merges 212)"),
    (205, "GitHub auth: seanpham99 via keyring; token scopes: gist, read:org, repo, workflow.", "github,auth,seanpham99", "keep; canonical auth fact"),
    (225, "Cron memory-housekeeping (id b7ba63551355) runs 2× daily at 11:00 and 23:00, uses managing-holographic-memory skill, AI-driven cleanup.", "cron,memory-housekeeping,holographic", "keep; canonical housekeeping cron (merges 160/235)"),
    (233, "/holographic-memory clean = junk removal + SQLite VACUUM only; dedup removed (content UNIQUE constraint prevents exact duplicates).", "holographic,clean,vacuum", "keep; canonical clean action (contradicts stale 220)"),
    (247, "9router-embeddings skill configured; endpoint $NINEROUTER_URL/v1/embeddings; supports OpenAI/Gemini/Mistral/Voyage/Nvidia.", "9router,embeddings,skill", "keep; canonical"),
]

removed = 0
for fid, reason in REMOVE:
    try:
        if store.remove_fact(fid):
            removed += 1
        else:
            print(f"WARN: fact {fid} not found (already removed?)")
    except Exception as e:
        print(f"ERROR removing {fid}: {e}")

updated = 0
for fid, content, tags, reason in UPDATE:
    try:
        if store.update_fact(fid, content=content, tags=tags, category=None):
            updated += 1
        else:
            print(f"WARN: fact {fid} not found for update")
    except Exception as e:
        print(f"ERROR updating {fid}: {e}")

clean_result = store.clean()
print(f"removed={removed} updated={updated}")
print(f"clean={clean_result}")

total = store._conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
print(f"facts_remaining={total}")
