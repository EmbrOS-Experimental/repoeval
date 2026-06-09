<div align="center">

# 🏆 RepoEval

**Turn Your Repo History Into a Coding Agent Benchmark**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-32%2F32%E2%9C%93-success.svg)](tests/)
[![EmbrOS](https://img.shields.io/badge/built%20by-embros.xyz-orange.svg)](https://embros.xyz)

*"Which coding agent is best at fixing MY bugs?"*

[Features](#features) • [Quick Start](#quick-start) • [CLI Usage](#cli-usage) • [How It Works](#how-it-works) • [AgentScope](#agentscope-integration)

</div>

---

## The Problem

You're choosing between Claude, Codex, GPT-4, Gemini for coding tasks. Benchmarks like SWE-bench tell you how they perform on **Django's issues**. 

But you don't work on Django. **You work on YOUR repo.**

## The Solution

RepoEval turns **your own GitHub issues, bug-fix PRs, and failing tests** into a repeatable benchmark. Point it at your repo, run any agent against the tasks, and get a leaderboard that actually matters to you.

```bash
# Install
pip install repoeval

# Import tasks from your repo's bug-fix history
repoeval import-git ./my-repo --output tasks.json

# Run benchmark
repoeval run tasks.json --agent shell --command "aider --model claude-sonnet-4"

# Generate leaderboard
repoeval report results.json --output ./leaderboard
```

<div align="center">

### 📊 Benchmark YOUR repo, not someone else's
### 🔄 Repeatable — same tasks, every run
### 📈 Compare agents head-to-head
### 🏆 Beautiful static HTML leaderboards

</div>

## Features

| Feature | Description |
|---------|-------------|
| 📥 **GitHub Importer** | Pull closed issues from any GitHub repo via API |
| 🔀 **Git History Importer** | Find bug-fix commits in your local repo automatically |
| 📋 **SWE-bench Compatible** | Import existing SWE-bench datasets |
| 🤖 **Agent Agnostic** | Run Aider, custom shell scripts, or any CLI agent |
| 🧪 **Test Scoring** | Run gold tests and measure pass/fail |
| 📝 **Patch Scoring** | Compare generated vs gold patches with diff similarity |
| 🏆 **Leaderboard** | Static HTML + JSON results, works on GitHub Pages |
| 🔄 **Comparison** | Compare multiple runs side-by-side |
| 📦 **Cross-platform** | Windows, macOS, Linux — pure Python |

## Quick Start

### 1. Install

```bash
pip install repoeval
```

### 2. Import Tasks

**From GitHub issues:**
```bash
repoeval import-github owner/repo --labels bug --max-issues 50 --output tasks.json
```

**From local git history:**
```bash
repoeval import-git ./my-project --max-commits 20 --output tasks.json
```

**From SWE-bench:**
```bash
repoeval run swe_bench_tasks.json --agent shell --command "aider"
```

### 3. Run Benchmark

```bash
# Simple shell command as agent
repoeval run tasks.json --agent shell --command "python fix.py"

# With a specific model
repoeval run tasks.json --agent aider --model claude-sonnet-4

# Limit tasks for a quick test
repoeval run tasks.json --max-tasks 5
```

### 4. Generate Leaderboard

```bash
repoeval report results.json ./leaderboard "My Benchmark"
# → ./leaderboard/index.html
# → ./leaderboard/results.json
```

### 5. Compare Runs

```bash
repoeval compare results-claude.json results-gpt4.json results-codex.json \
    --title "Claude vs GPT-4 vs Codex" \
    --output ./comparison
```

## CLI Usage

```
Usage: repoeval [OPTIONS] COMMAND [ARGS]...

  RepoEval — Turn your repo history into coding agent benchmarks.

Commands:
  run             Run a benchmark against tasks
  import-git      Import tasks from git history (bug-fix commits)
  import-github   Import tasks from GitHub issues
  report          Generate leaderboard from results JSON
  compare         Compare multiple benchmark result files
  validate        Validate a tasks JSON file
```

## How It Works

```
┌─────────────┐     ┌──────────┐     ┌──────────┐     ┌────────────┐
│ GitHub / Git │────>│  Tasks   │────>│  Agent   │────>│  Results   │
│  History     │     │  Schema  │     │  Runner  │     │  + Scores  │
└─────────────┘     └──────────┘     └──────────┘     └─────────────┘
                                                                │
                           ┌────────────────────────────────────┘
                           ▼
                    ┌──────────────┐
                    │  Leaderboard │
                    │  HTML + JSON │
                    └──────────────┘
```

## Task Schema

Each benchmark task follows the SWE-bench format:

```json
{
  "instance_id": "django__django-12345",
  "repo": "django/django",
  "base_commit": "abc1234",
  "issue_title": "Fix the queryset bug",
  "issue_body": "When filtering with None...",
  "test_patch": "@@ -10,3 +10,3 @@\n-old\n+new",
  "FAIL_TO_PASS": ["tests/test_qs.py::test_filter"]
}
```

## Scoring

RepoEval uses two scoring methods:

1. **Test-Based (70%)** — Run the gold test commands after the agent fixes the issue. Did all tests pass?
2. **Patch-Based (30%)** — Compare the agent's generated diff against the gold diff using sequence matching.

Combined score = `0.7 * test_score + 0.3 * patch_score`

## AgentScope Integration

RepoEval pairs perfectly with [AgentScope](https://github.com/EmbrOS-Experimental/agent-scope):

1. **AgentScope** — Capture and debug individual agent runs
2. **RepoEval** — Benchmark and compare across many runs

Together they tell the full story: *"Not only did my agent pass 7/10 tasks, but here's exactly where it failed on task #3."*

## Built By

RepoEval is built by the team behind [EmbrOS](https://embros.xyz) — the AI Builder Operating System.

We needed a way to evaluate coding agents on our own codebase. Nothing existed. So we built it.

## License

Apache-2.0 — free to use, modify, and contribute.

## Contributing

PRs welcome! See [CONTRIBUTING.md](CONTRIBUTING.md).

<div align="center">

**Star this repo if you think your repo deserves its own benchmark ⭐**

[🐦 Twitter](https://x.com/embOS_ai) • [💬 Discord](https://discord.gg/FZsWkYpM9b) • [🌐 embros.xyz](https://embros.xyz) • [🔭 AgentScope](https://github.com/EmbrOS-Experimental/agent-scope)

</div>
