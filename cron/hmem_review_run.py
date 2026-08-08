#!/usr/bin/env python
"""Holographic memory review run 2026-07-31: junk/dup/stale removal + consolidation."""
import sys

sys.path.insert(0, "/home/sonpham/.hermes/hermes-agent")

from plugins.memory import load_memory_provider

p = load_memory_provider("hrr_memory")
p.initialize(session_id="cron-hmem-review-run")
store = p._store
conn = store._conn

# --- REMOVE: session logs, PR/commit ephemera, market snapshots, test counts,
#     self-referential pointers, exact dups of kept facts / regular memory /
#     skill docs. Verified against full DB dump this session.
REMOVE = [
    28,    # skill category inventory (stale; now 31 entries)
    77,    # vnstock modular API claim — CONTRADICTED by 430 (explorer imports required); trust 0.3
    79,    # PR #74020 pyproject fix detail (ephemeral)
    80,    # gateway exit-0 regression-test detail (ephemeral PR detail)
    255,   # cron self-log dup of 225
    256,   # cron self-log dup of 225
    257,   # cron self-log dup of 225
    258,   # log of past HRR fix (in regular memory)
    259,   # housekeeping run log
    260,   # housekeeping run log
    261,   # housekeeping run log (VACUUM reclaimed 12KB)
    262,   # meta note on entity:cron scan (in regular memory)
    263,   # cron log dir (ephemeral)
    265,   # 9router dup of 18
    266,   # repo/remote dup of 125
    267,   # PR #74900 state ephemera
    268,   # PR #75251 state ephemera
    269,   # PR #75252 state ephemera
    271,   # ui-tui test runner note (ephemeral)
    272,   # test count ephemera
    273,   # commit detail ephemera
    275,   # approval note (ephemeral)
    276,   # hermes update source — CONTRADICTS 330; both ephemera, covered by 125
    277,   # PR #74900 state ephemera
    278,   # PR #74900 file list (ephemeral)
    279,   # PR #75251 head ephemera
    280,   # PR #75252 head ephemera
    281,   # PR #73210 head ephemera
    282,   # branch-cut analysis ephemera
    283,   # review-comment obsolescence ephemera
    284,   # merge state ephemera
    285,   # son/dev commit-diff ephemera
    286,   # son/dev vs upstream ephemera
    287,   # hermes update restart note (dup of 125/330)
    288,   # PR #74020 identification ephemera
    289,   # PR author identity ephemera
    290,   # PR #74020 head ephemera
    291,   # #75251 topic ephemera
    292,   # review comments ephemera
    293,   # comment 3684533036 detail ephemera
    294,   # comment 3684533040 detail ephemera
    295,   # fix commit detail ephemera
    296,   # git sync state ephemera
    297,   # working-tree state ephemera
    298,   # branch deletion ephemera
    299,   # branch list ephemera
    300,   # CaptureEngine location ephemera
    301,   # PluginLlm location ephemera
    302,   # provider loading internals ephemera
    303,   # initialize() kwargs ephemera
    304,   # design decision ephemera (shipped)
    305,   # hook point line numbers ephemera
    307,   # store tool list (self-referential)
    308,   # test count ephemera
    309,   # repo identity dup of 125
    312,   # js-autofix root cause — documented in github-actions-debugging/references/js-autofix-fork-case.md
    313,   # upstream token migration — in skill ref doc
    314,   # APP_PRIVATE_KEY fix — in skill ref doc
    315,   # composite action secrets — in skill ref doc
    316,   # trusted-automation env — in skill ref doc
    317,   # skill ref pointer (self-referential)
    318,   # leftover branch note (ephemeral)
    319,   # repo environments inventory (ephemeral)
    320,   # fork PR hygiene dup of 125
    321,   # user/remote dup of 125/205/83
    322,   # 5-PR inventory — supersedes 75; 75 updated instead
    323,   # reviewer comments ephemera
    324,   # #74020 rebase ephemera
    325,   # #73210 branch ephemera
    326,   # SBERT layer merge ephemera
    327,   # son/dev reset ephemera
    328,   # branch deletion dup of 298
    329,   # test suite counts ephemera
    330,   # hermes update origin — CONTRADICTS 276; covered by 125
    331,   # uv/pytest setup ephemera
    332,   # working tree state dup of 297
    333,   # PR #75252 OPEN state ephemera
    334,   # .gitignore absence ephemera
    335,   # local stopgap ephemera
    336,   # son/dev decision ephemera
    337,   # main vs son/dev ephemera
    338,   # config provider ephemera
    339,   # son/dev superset ephemera
    340,   # branch strategy dup of 125
    343,   # portal repo URL+clone path dup of 341 (path absorbed into 341)
    344,   # portal empty-repo state (ephemeral; now stale)
    345,   # Luca/Harshit/Yuri AI agents — dup of 47
    346,   # n8n tickets obsolete — absorbed into 46
    347,   # Jira status — absorbed into 46
    353,   # user home dup of 391/404
    358,   # self-referential pointer to 349
    359,   # self-referential pointer to 348
    361,   # Slack send path — merged into 375
    362,   # bot token scopes — merged into 375
    363,   # Slack MCP read-only dup of 354
    365,   # message ts (ephemeral)
    367,   # working dir (ephemeral)
    368,   # pending items (ephemeral)
    371,   # slack skill inventory (ephemeral)
    373,   # skill file path dup of 372
    374,   # Slack MCP read-only dup of 354
    376,   # bot-token failure path — merged into 375
    377,   # skill patch log (ephemeral)
    378,   # outcome log (ephemeral)
    381,   # skills architecture dup of 379
    382,   # bundled skills dup of 379
    383,   # npx update dup of 379
    384,   # skill count inventory (ephemeral)
    385,   # adapted-skill inventory (ephemeral)
    386,   # caveman skills absence (ephemeral)
    387,   # skills-tidy path dup of regular memory
    388,   # category dir inventory (ephemeral)
    391,   # user home dup of 404
    392,   # environment dup (trivial)
    393,   # canonical store dup of 379
    394,   # symlink target dup of 379
    395,   # bundled skills dup of 379
    396,   # npx update dup of 379
    397,   # adapted dirs dup of 379
    398,   # near-dup review flag (ephemeral)
    399,   # tidy script dup of 387
    400,   # tree inventory (ephemeral)
    401,   # single-skill category (ephemeral)
    402,   # mislink fix log (ephemeral; lesson kept in 389)
    404,   # user home dup
    407,   # vnstock community key dup of regular memory
    408,   # OpenBB no-VN dup of regular memory
    409,   # openbb-tmx dup of 408
    410,   # finance-data skill creation log — dup of 405
    412,   # edgartools set_identity — documented in finance-data skill
    413,   # ~/.venv install log — dup of 405
    414,   # session log (ephemeral)
    415,   # session analysis summary (ephemeral)
    417,   # self-referential "fact id 405 stored"
    419,   # Tuan Le Vietnamese pref dup of user profile
    420,   # smart-money pref dup of user profile
    421,   # framework note dup of user profile
    422,   # HPG market snapshot (ephemeral)
    423,   # VNM market snapshot (ephemeral)
    424,   # HPG earnings snapshot (stale-prone)
    425,   # VNM earnings snapshot (stale-prone)
    426,   # foreign-flow snapshot (ephemeral)
    427,   # VIC price snapshot (ephemeral)
    428,   # BTC price snapshot (ephemeral)
    429,   # env tool listing (ephemeral)
    435,   # two-account note dup of 433/434
    436,   # org-owned repo dup of 433
    437,   # token scopes (discoverable via gh auth status)
    434,   # gh-auth-switch dup of 433
    439,   # pull commit head (ephemeral)
    442,   # label creation log (ephemeral)
    443,   # issue creation log (ephemeral; on GitHub)
    444,   # self-referential "fact store IDs saved"
    450,   # session key (ephemeral)
    451,   # session storage paths (ephemeral)
    452,   # PR #94 state (ephemeral; on GitHub)
    453,   # issues-updated log (ephemeral)
    454,   # dbo 100 tables — dup of 448 + docs map
    455,   # Analyst/Researcher fields — dup of 448
    456,   # R_TargetPrice stats — in docs map
    457,   # R_FinancialMetrics stats — in docs map
    458,   # R_FactAnalyst stats — in docs map
    459,   # FactNAV stats — in docs map
    460,   # R_* layer detail — in docs map
    461,   # Fact* layer detail — in docs map
    462,   # LVF_* staleness — in docs map
    463,   # MarketCapInfo broken — in docs map
    464,   # TradeTrans detail — in docs map
    465,   # procs inventory — in docs map
    466,   # views inventory — in docs map
    467,   # FKs inventory — in docs map
    468,   # deliverable path dup of 448
    469,   # project_intraday path dup of 449
    470,   # project_intraday detail dup of 449
    471,   # self-referential stored-facts list
    473,   # session-compaction note (ephemeral)
]

# --- UPDATE: consolidate + rebucket kept facts into proper categories
# (content, tags, category, reason) — content=None keeps existing text
UPDATE = [
    (341, "PTG client portal repo: github.com/Automation-Architecture/ptg-client-portal, cloned /home/sonpham/Works/ptg-client-portal. Created by Brad 2026-07-31; multitenant portal for hotel clients to review/approve published content. Access granted to Sean + Khang.",
     "ptg,client-portal,repo", "project", "absorb 343 clone path; drop brand-new 3-min age"),
    (46, "PTG Jira: 50 tickets, 8 open; Sean's tickets (PTG-231/232/233/181) misassigned — needs reassign before working. n8n-era tickets PTG-240/241 obsolete (n8n retired, Brad 2026-07-31). Current: PTG-232/233 Done, PTG-231 To Do (assigned to Brad), PTG-180/181 untouched, PTG-218/219/222/223 WIP since Jun 27.",
     "ptg,jira,tickets,backlog", "project", "absorb 346/347; drop stale key-open list"),
    (75, "PRs by seanpham99 on NousResearch/hermes-agent: #73210 (gateway exit-0 fix), #74020 (holographic auto-capture), #74900 (TUI visualizer), #75251 (TUI SSH Ctrl+J fix), #75252 (.gitignore .codegraph/). #74891 closed as duplicate of #74900.",
     "pr,hermes-agent,nousresearch,seanpham99,inventory", "general", "absorb 322; add 75251/75252"),
    (348, "Client portal MVP flow: Property → Scrape → Generate → Internal Review → Send to Approver → OTP Login → Review Current vs Proposed → Sign and Approve. Flow NOT proposed by Inga — attribution was a mistake, keep neutral.",
     "ptg,client-portal,flow", "project", "drop deadline tail (349 canonical)"),
    (375, "Slack send path: `chat.postMessage` with `SLACK_USER_OAUTH_TOKEN` (xoxp, ~/.hermes/.env), posts as user via chat:write scope. `hermes send --to slack:<channel>` uses xoxb bot token and fails `not_in_channel` when bot absent.",
     "slack,send,chat.postmessage,xoxp", "tool", "merge 361+376"),
    (264, None, "hermes,approvals,hardline,security", "tool", "rebucket"),
    (270, None, "hermes,codegraph,gitignore", "project", "rebucket"),
    (274, None, "gh,cli,pr,quirk", "tool", "rebucket"),
    (306, None, "holographic,config,memory", "tool", "rebucket"),
    (310, None, "github,ci,js-autofix,fork", "tool", "rebucket"),
    (311, None, "github,ci,js-autofix,fork", "tool", "rebucket"),
    (342, None, "ptg,repos,architecture", "project", "rebucket"),
    (349, None, "ptg,client-portal,deadline", "project", "rebucket"),
    (350, None, "ptg,apps,architecture", "project", "rebucket"),
    (351, None, "ptg,team,product", "project", "rebucket"),
    (352, None, "ptg,slack,sprint", "project", "rebucket"),
    (355, None, "ptg,slack,workspace", "project", "rebucket"),
    (356, None, "user,slack,identity", "general", "rebucket"),
    (357, None, "ptg,slack,people", "project", "rebucket"),
    (360, None, "ptg,slack,channels", "project", "rebucket"),
    (364, None, "hermes,slack,send,cli", "tool", "rebucket"),
    (366, None, "hermes,env,config,terminal", "tool", "rebucket"),
    (369, None, "slack,bot,identity", "tool", "rebucket"),
    (370, None, "skills,user-preference", "user_pref", "rebucket"),
    (372, None, "slack,skill,send", "tool", "rebucket"),
    (389, None, "skills,symlinks,npx,lesson", "tool", "rebucket"),
    (390, None, "skills,symlinks,npx,lesson", "tool", "rebucket"),
    (403, None, "skills,organization,user-preference", "user_pref", "rebucket"),
    (411, None, "skills,authoring,convention", "tool", "rebucket"),
    (416, None, "hermes,sandbox,filesystem,quirk", "tool", "rebucket"),
    (418, None, "tuanle,analysis,method", "user_pref", "rebucket"),
    (438, None, "vnam,data-pipeline,path", "project", "rebucket"),
    (440, None, "vnam,data-pipeline,coverage", "project", "rebucket"),
    (441, None, "vnam,data-pipeline,mssql,schema", "project", "rebucket"),
    (472, None, "user-preference,planning", "user_pref", "rebucket"),
]

before = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]

removed = 0
missing = []
for fid in REMOVE:
    if store.remove_fact(fid):
        removed += 1
    else:
        missing.append(fid)

updated = 0
for fid, content, tags, cat, reason in UPDATE:
    if store.update_fact(fid, content=content, tags=tags, category=cat):
        updated += 1
    else:
        missing.append(fid)

clean_result = store.clean()

after = conn.execute("SELECT COUNT(*) FROM facts").fetchone()[0]
no_hrr = conn.execute("SELECT COUNT(*) FROM facts WHERE hrr_vector IS NULL").fetchone()[0]
no_sbert = conn.execute("SELECT COUNT(*) FROM facts WHERE sbert_vector IS NULL").fetchone()[0]
cats = conn.execute("SELECT category, COUNT(*) FROM facts GROUP BY category ORDER BY COUNT(*) DESC").fetchall()

print(f"before={before} removed={removed} updated={updated} after={after}")
print(f"missing_ids={missing}")
print(f"clean={clean_result}")
print(f"no_hrr={no_hrr} no_sbert={no_sbert}")
print("categories:", {r['category']: r['COUNT(*)'] for r in cats})
