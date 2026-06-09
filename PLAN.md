# RepoEval — Plan

## Priority Score: 90/100
Impact: 4.5 | Novelty: 4.5 | Virality: 5.0

## Elevator Pitch
**Turn your own repository history into a repeatable benchmark for coding agents and models.**

## What It Does
Point RepoEval at your repo → it imports historical issues, failing tests, bug-fix PRs → spins up containers → runs multiple agents/models against the same tasks → publishes a leaderboard.

## Why Now
- SWE-bench proved benchmarking models on real GitHub issues works
- Inspect AI and OpenAI Evals provide the scaffolding
- But nobody made it easy to benchmark YOUR repo specifically

## Core Features
1. **Task Importer** — Pull issues, PRs, failing tests from GitHub or local git
2. **Agent Adapters** — Run Aider, OpenHands, Continue, custom agents against tasks
3. **Containerized Execution** — Docker-based isolation per task
4. **Leaderboard** — Static HTML + JSON results, pass rate, cost, latency
5. **CI Gating** — Fail CI if agent performance drops below threshold

## Stack
- **Python** — ecosystem fit (SWE-bench, Inspect AI patterns)
- **Docker** — containerized task execution
- **Static HTML** — leaderboard (no backend needed for MVP)
- **GitHub Actions** / **CLI** — trigger benchmarks in CI or locally

## MVP Milestones

### Month 1: Task Schema + Importer
- [ ] Define SWE-bench-style task schema (repo, issue, base_commit, test_patch)
- [ ] GitHub issue/PR importer (REST + GraphQL)
- [ ] Local git history importer (parse commits for bug-fix patterns)
- [ ] JSON/YAML task file format

### Month 1-2: Execution Engine
- [ ] Docker container per task (checkout base commit, apply agent)
- [ ] Agent runner interface (subprocess-based)
- [ ] Aider adapter (CLI invocation + output parsing)
- [ ] Generic shell adapter (run any command)

### Month 2: Scoring + Leaderboard
- [ ] Test-based scoring (pass/fail against gold tests)
- [ ] Patch correctness scoring (diff comparison)
- [ ] Token + cost tracking per task
- [ ] Static HTML leaderboard (GitHub Pages friendly)
- [ ] JSON export for programmatic access

### Month 2-3: CI + Polish
- [ ] GitHub Actions integration
- [ ] CLI: `repoeval run`, `repoeval report`, `repoeval compare`
- [ ] Leaderboard comparison (run A vs run B)
- [ ] Dataset versioning + holdout sets

## Effort
- Solo MVP: 2–3 PM
- Team of 3: 4–5 PM (~4-6 weeks elapsed)

## AgentScope Integration
RepoEval complements AgentScope perfectly:
- **AgentScope** → replay & debug individual runs
- **RepoEval** → benchmark & compare across runs

Together: *"Run your agent → capture with AgentScope → benchmark with RepoEval → compare on leaderboard"*

## Virality Hooks
- "Claude vs Codex vs Gemini on my actual monorepo"
- "Which agent is best at flaky-test fixes?"
- "Top open-source coding agents ranked on a real Rust repo"

## License
Apache-2.0
