# RepoEval — Vision

## Elevator Pitch
Turn your own repository history into a **repeatable benchmark** for coding agents and models.

## The Problem
SWE-bench proved you can test models on real GitHub issues. SWE-bench Verified curated a better subset. Inspect AI and OpenAI Evals provide eval frameworks. But nothing says **"benchmark MY repo before I trust an agent on it."** That's the product gap.

## User Stories
1. A maintainer points RepoEval at a repo, imports historical issues / failing tests / bug-fix PRs
2. RepoEval spins up containers, runs multiple agents/models against the same tasks
3. Reports: pass rate, patch correctness, latency, cost → publishes a leaderboard the team trusts because it's built from THEIR codebase and THEIR workflow

## Core Features
- **Task importer**: from GitHub issues, PR history, curated task lists
- **Standardized task schema**: SWE-bench-style
- **Multi-agent/model runner**: containerized execution
- **Scoring**: pass rate, patch correctness, tool usage, cost leaderboard
- **CI integration**: gate deployments on benchmark results
- **Holdout task sets**: prevent benchmark gaming

## What Makes It Different
- Repo-specific, not generic — benchmarks against YOUR codebase
- Multi-model comparison on identical tasks
- Evidence-preserved: task-level results, not just aggregate scores
- CI-first: run in CI gate, not just local experimentation

## Virality Hooks
- "Claude vs Codex vs Gemini on my actual monorepo"
- "Which agent is best at flaky-test fixes?"
- "Top open-source coding agents ranked on a real Rust repo"

## License
MIT or Apache-2.0

## Monetization
Hosted benchmark runs, private leaderboards, scheduled evaluations, CI policy gates, enterprise reporting
