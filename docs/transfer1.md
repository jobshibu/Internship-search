# Internship Pipeline — Transfer to Claude Code

Oct 15, 2026

## Purpose

This is your guide for building the daily internship pipeline yourself, from scratch, with Claude Code as a mentor rather than the author. It covers what to build in what order, the decisions already made, the traps in the source data, and how to deploy and explain it.

Goal: a public, data-engineering-grade pipeline (GitHub Actions → Postgres → Streamlit dashboard) you can demo and explain in tomorrow's data engineer intern interview.

## Where it started

Today the search runs as the Cowork scheduled task "Internship search afternoon" (`trig_01XC9eNBgDttESXChLGS4QXH`), daily at 1:00 pm America/Chicago. It keeps state in Google Drive and rewrites its own prompt each run to point at the newest CSV.

| Item | Value |
| --- | --- |
| Current tracker CSV (Google Sheet) | `1p4iYSmapXXijK-I8-YlzZoFXBqngaS_CiintXmHt3VE` |
| Main "Internship Tracker" folder | `1L_QCd7FUqbiBJ6kzfZNqzXiBBSF--1Vu` |
| "data" subfolder | `15JrnXpx3uTaS2vStwoVwGNc5Ucg273Z0` |
| Rows as of the Oct 14, 2026 run | 216 (210 open, 6 applied) |
| CSV columns | Company, Role, Location, Pay, Duration, Deadline, Link, Resume Match, Status, Posted Date, Date Found, Notes |

Keep the scheduled task running until the new pipeline has completed a few clean daily runs, then disable it. Export the latest sheet as CSV to seed the new database.

## Architecture and decisions

The stack is Python ETL on GitHub Actions, writing to Supabase Postgres, read by a public Streamlit app — chosen for a free, explainable, data-engineering-shaped project by tomorrow.

```
GitHub lists            Daily GitHub Action          Supabase Postgres              
(SimplifyJobs,   --->   Extract                ---> Bronze      raw_listings
 vanshb03,              -> Parse                    Quarantine  rejected_listings
 sndsh404)              -> Validate + score         Ops         pipeline_runs
                              |                     Silver      listings, sources
                              v                     Gold        views for the app  ---> Streamlit app
                        Slack digest (optional)                                         (public, read-only)
```

Each run writes every parsed row to bronze, valid rows to silver, and rejects to quarantine, in one transaction; the app reads only gold views.

| Decision | Choice | Why |
| --- | --- | --- |
| Scheduler | GitHub Actions cron, 1 pm CT | Free, versioned with the code, run logs built in |
| Database | Supabase Postgres (SQLite locally) | Free, browsable table UI, reachable from Actions and Streamlit |
| Logic | Deterministic Python, no LLM | No API key or cost; anyone can fork and run it |
| Dedup key | sha1 of the normalized application link | One posting listed by several sources becomes one row |
| Match tier | Keyword profile in `config.py` (high / medium / low / other) | Same rules as the current Resume Match column, now configurable |
| Dashboard | Streamlit Community Cloud, read-only DB role | Public link in minutes; least-privilege access |
| Private data | Application status stays out of the public DB | The board is shared; your applications are not |

## Build plan

Milestones 1–6 give you a working, deployed, demoable pipeline in roughly 6–7 hours (rough guesses); stop there if time runs out and do the README. Finish each "Done when" check before moving on.

1. **Skeleton and table design** (~45 min)
    - Create the repo, a virtualenv, and a `pipeline/` package. Use SQLite locally.
    - Design the `listings` table on paper first. Ask yourself: what makes two rows the same posting? (Hint: not company + role.)
    - Done when: one command creates your tables in a local SQLite file.
2. **Extract and parse one source: SimplifyJobs** (~1.5 h)
    - Download the raw README with `requests`; parse its HTML tables with BeautifulSoup.
    - Handle the quirks in "Source formats" below: `↳` rows, multi-location `<details>`, the second (Simplify) link.
    - Done when: you get ~1,900 rows and five spot-checks match the GitHub page.
3. **Transform and validate** (~1.5 h)
    - Normalize links, filter to US, drop 🎓 and closed rows, turn `3d` / `1mo` into dates, assign a match tier from keywords.
    - Never silently drop a row: keep each reject with a reason.
    - Write a pytest test for each gotcha listed below.
    - Done when: counts per reject reason look sane and the tests pass.
4. **Load idempotently** (~1 h)
    - Upsert with `INSERT … ON CONFLICT`. Decide which columns update on conflict and which are write-once (`first_seen_at`, `posted_date`).
    - Record each run in a `pipeline_runs` table with counts and status.
    - Done when: running twice in a row reports 0 new listings the second time.
5. **Dashboard** (~1 h)
    - Streamlit, read-only: posted-today table on top, filters, clickable links, new-per-day chart.
    - Done when: it runs locally against your database.
6. **Deploy** (~1 h)
    - Follow "Setup and deploy" below: Supabase, GitHub Actions secrets and cron, Streamlit Community Cloud.
    - Done when: a manual workflow run goes green and the public URL shows data.
7. **Stretch, if time allows**
    - Add the two markdown sources (one parser for pipe tables), a bronze `raw_listings` table, closing listings that disappear, seeding your old tracker CSV, a Slack digest.
8. **README before the interview** — the architecture diagram, how to run it, and the decision table from this doc.

## Source formats and gotchas

The three sources use different formats, and each hides a bug worth knowing before you build.

| Source | Format | Date column | Quirks |
| --- | --- | --- | --- |
| [SimplifyJobs](https://github.com/SimplifyJobs/Summer2027-Internships) (primary volume) | HTML `<table>` under `## <category>` headings (5 categories) | Age: `0d` … `30d`, then `1mo` … | `↳` = same company as row above; 🔥 before company; multi-location in `<details><summary>N locations</summary>A<br>B</details>`; second link is simplify.jobs (skip it) |
| [vanshb03](https://github.com/vanshb03/Summer2027-Internships) | Markdown pipe table | `Aug 21` (no year) | Last updated Aug 21, so it never has `0d` rows; closed rows show 🔒 instead of a link; `**31 locations**` prefix in location cells |
| [sndsh404](https://github.com/sndsh404/summer-2027-internships) | Markdown pipe table | ISO `2026-07-21` or `-` | Locations joined with ` / `; README also contains a "tracker" section unrelated to the table |

Markers in role text: 🎓 advanced degree, 🛂 no sponsorship, 🇺🇸 US citizenship, 🔒 closed.

Traps found by testing against the live lists — write a test for each:

- **Substring location match.** Matching "uk" as a substring flagged Milwa*uk*ee, WI as non-US. Use word-boundary regex.
- **Query stripping collides postings.** Dropping every query param makes all Greenhouse embed links (`job_app?token=…`) and Taleo links (`?job=343299`) one key. Keep identifying params: `token`, `gh_jid`, `job`, `jobid`, `id`, `req`.
- **Opaque job IDs.** Jobvite `/job/oMAPAfwv` and applytojob `/apply/oaG5GcybAo` are real postings with no digits-only ID; accept mixed-case tokens of 6+ characters after `/job/` or `/apply/`.
- **Search pages slip into lists.** vanshb03 links Microsoft roles to a careers search URL; the URL validator correctly quarantines them.

## Setup and deploy

All three services have free tiers that cover this project; you create the accounts and write the code.

1. **Repo.** Create a public GitHub repo (e.g. `internship-pipeline`), clone it, open Claude Code inside it.
2. **Local first.** `python -m venv .venv`, `pip install -r requirements.txt`. With no `DATABASE_URL` set, everything runs on `sqlite:///internships.db`.
3. **Seed.** Export the current tracker sheet as CSV into `data/legacy_tracker.csv` and load it with a seed script you write. Leave the Status column out of the public tables — your applications stay private.
4. **Run locally.** `python -m pipeline.run`, then run it again: the second run should report 0 new rows (idempotency check).
5. **Supabase.** New project → Settings → Database → copy the Session pooler connection string. Point your table-creation script at that `DATABASE_URL`, then create any views in the SQL editor. Create a read-only role for the dashboard.
6. **GitHub Actions.** Add repo secrets `DATABASE_URL` (write role) and optional `SLACK_WEBHOOK_URL`. The workflow runs tests on push, the pipeline on cron `0 18 * * *` (1 pm CDT) and on manual dispatch, with `concurrency` set so two runs never overlap.
7. **Dashboard.** Deploy `dashboard/app.py` on [Streamlit Community Cloud](https://streamlit.io/cloud) from the repo; put the read-only `DATABASE_URL` in the app's secrets. Share that URL publicly.
8. **Cut over.** After 2–3 clean scheduled runs, disable the Cowork task.

Open question: Supabase free projects pause after a week of no activity; the daily job keeps it awake, but confirm on Supabase's pricing page before relying on it.

## Using Claude Code as your mentor

Save this doc in your repo as `docs/TRANSFER.md`, then paste the prompt below as your first message in Claude Code. It sets Claude Code up to coach, review and quiz you instead of writing the pipeline.

```markdown
You are my mentor while I build the project in docs/TRANSFER.md myself. I have a
data engineer intern interview tomorrow and need to understand and explain every line.

Rules:
- Do not write implementation code or edit my files unless I explicitly say "write it".
- When I'm stuck: ask what I tried, then give the smallest useful hint. Escalate only
  if I ask: concept -> docs link -> pseudocode -> a tiny example on toy data.
- When I say "review": read my changes (git diff), check them against the milestone's
  "Done when" and the gotchas in TRANSFER.md, and list issues by severity. Don't fix them.
- Explain the why: tradeoffs, and what a senior data engineer would do differently.
- After each milestone, ask me 2-3 interview questions about what I just built.

Start by asking which milestone I'm on.
```

Useful requests along the way: "review", "hint", "explain upserts like I'm new to Postgres", "quiz me on milestone 4", "what would break if this ran twice at once?"

## Interview talking points

Lead with the problem and one number, then go deeper wherever the interviewer leans in.

- **The pitch.** "I turned a manual internship hunt into a daily ETL pipeline: three community GitHub lists in, about 1,700 validated US postings out, deduplicated across sources, on a public dashboard."
- **Medallion layers.** Bronze keeps every parsed row as JSON per run, so transform rules can change and history can be replayed. Silver is one row per posting. Gold is views for the dashboard.
- **Idempotency.** The key is a hash of the normalized link; loads are `INSERT … ON CONFLICT DO UPDATE`. Rerunning a day changes nothing. `posted_date` and `first_seen_at` are write-once.
- **Atomicity.** Each run's load is one transaction; a crash leaves the database as it was, and the `pipeline_runs` row records the failure.
- **Quarantine, not silent drops.** Every rejected row lands in `rejected_listings` with a reason (`non_us`, `generic_url`, `advanced_degree_required`, `closed`), so filter rules are auditable.
- **Schema-drift detection.** Each source has a minimum row count; if a README's format changes and the parser finds nothing, the run is marked degraded instead of quietly loading zero rows.
- **Safe deletes.** A posting closes only when every source that reported it was fetched healthily, so a flaky source never causes false closures.
- **Real bugs found by testing on live data.** The Milwaukee/"uk" substring bug and the query-param collision are concrete stories of why you test against production data.
- **What you'd do next.** Alembic migrations instead of `create_all`, dbt for the gold layer, an orchestrator (Dagster/Airflow) once there are dependencies between jobs, and per-user application tracking with auth.
