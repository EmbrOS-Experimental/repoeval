<div align="center">

# 🏆 RepoEval

**Turn Your Repo History Into a Coding Agent Benchmark**

[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.9%2B-brightgreen.svg)](https://python.org)
[![Tests](https://img.shields.io/badge/tests-32%2F32%E2%9C%93-success.svg)](tests/)
[![EmbrOS](https://img.shields.io/badge/built%20by-embros.xyz-orange.svg)](https://embros.xyz)

*"Which coding agent is best at fixing MY bugs?"*

</div>

---

## What Is RepoEval?

You're choosing between Claude, Codex, GPT-4, Gemini for coding tasks. SWE-bench tells you how they perform on **Django's issues**. But you don't work on Django — **you work on YOUR repo.**

RepoEval turns your own GitHub issues and bug-fix history into a repeatable benchmark. Run any agent against your tasks, get a leaderboard. No guesswork.

## Install

```bash
pip install repoeval
```

## Full Walkthrough (Copy-Paste Ready)

### Option A: Benchmark from GitHub Issues (Recommended)

```bash
# 1. Import closed bug issues from any repo
repoeval import-github django django --labels bug --max-issues 10 --output tasks.json

# 2. Validate the tasks look correct
repoeval validate tasks.json
# ✓ Valid — 10 tasks

# 3. Run benchmark (uses shell command as agent)
repoeval run tasks.json --agent shell --command "echo would fix this" --output ./results

# 4. Generate leaderboard
repoeval report ./results/results.json --output ./leaderboard --title "Django Bug Benchmark"

# 5. Open the leaderboard in your browser
open ./leaderboard/index.html        # macOS
xdg-open ./leaderboard/index.html    # Linux
start ./leaderboard\index.html       # Windows
```

### Option B: Benchmark from Your Local Git History

```bash
# 1. Go to your repo
cd /path/to/your/project

# 2. Import bug-fix commits (requires commits with messages like "Fix #123", "Bugfix:", "Hotfix:")
repoeval import-git . --output tasks.json

# 3. Run benchmark
repoeval run tasks.json --agent shell --command "echo fix" --max-tasks 5 --output ./results

# 4. Generate leaderboard
repoeval report ./results/results.json --output ./leaderboard
```

> **Note:** `import-git` only finds commits whose messages match bug-fix patterns (e.g. "Fix #123", "Bugfix: crash", "Hotfix: security", "Closes #456"). If your commits say "Update code" or "WIP" they won't be detected. Use `import-github` instead — it works with any repo.

### Option C: Use Your Own Tasks File

Create `my-tasks.json`:

```json
[
  {
    "instance_id": "my-project-1",
    "repo": "/path/to/local/repo",
    "issue_title": "Login fails when token is null",
    "issue_body": "Users report 500 error on login when token is null. Need null check.",
    "gold_test_commands": ["pytest tests/test_login.py -v"],
    "difficulty": "easy",
    "tags": ["bugfix", "auth"]
  }
]
```

```bash
repoeval validate my-tasks.json
repoeval run my-tasks.json --agent shell --command "python fix.py" --output ./results
repoeval report ./results/results.json --output ./leaderboard
```

## Comparing Agents

Run the same tasks with different agents, then compare:

```bash
# Run with agent A
repoeval run tasks.json --agent shell --command "aider --model claude-sonnet-4" --output ./results-claude

# Run with agent B
repoeval run tasks.json --agent shell --command "aider --model gpt-4o" --output ./results-gpt4

# Compare side-by-side
repoeval compare ./results-claude/results.json ./results-gpt4/results.json --title "Claude vs GPT-4"
# → ./comparison/comparison.html
```

## Commands Reference

```
repoeval import-github <owner> <repo>    Import closed issues from GitHub
  --labels bug                            Filter by label (default: bug)
  --max-issues 50                         Limit number of issues
  --output tasks.json                     Output file
  --token $GITHUB_TOKEN                   GitHub API token (optional, for private repos)

repoeval import-git <path>               Import bug-fix commits from local git
  --max-commits 20                        Max commits to scan
  --output tasks.json                     Output file

repoeval run <tasks_file>                Run benchmark
  --agent shell                           Agent type (shell, aider)
  --command "echo fix"                    Shell command to run as agent
  --model claude-sonnet-4                 Model name (for aider)
  --max-tasks 5                           Limit tasks (0=all)
  --output ./results                      Output directory
  --name "My Benchmark"                   Run name

repoeval report <results_file>           Generate leaderboard
  --output ./leaderboard                  Output directory
  --title "My Benchmark"                 Leaderboard title

repoeval compare <results>...            Compare multiple runs
  --output ./comparison                   Output directory
  --title "Agent Comparison"              Comparison title

repoeval validate <tasks_file>           Validate tasks file
```

## What the Leaderboard Shows

```
┌─────────────────────────────────────────────────────┐
│ 🏆 Django Bug Benchmark                             │
│ 10 tasks · 3 passed · 7 failed · 30.0% pass rate   │
├────┬──────────────────────┬────────┬────────┬───────┤
│ #  │ Task                 │ Status │ Tests  │ Patch │
├────┼──────────────────────┼────────┼────────┼───────┤
│ 1  │ Fix queryset bug     │ passed │ 3/3    │ ✓     │
│ 2  │ Fix null check       │ passed │ 2/3    │ ✗     │
│ 3  │ Fix auth middleware  │ failed │ 0/3    │ ✗     │
│ .. │ ...                  │ ...    │ ...    │ ...   │
└────┴──────────────────────┴────────┴────────┴───────┘
```

Open `leaderboard/index.html` in any browser — it's a self-contained static file, no server needed.

## How Scoring Works

1. **Test-Based (70%)** — After the agent "fixes" the issue, run the gold tests. Did they pass?
2. **Patch-Based (30%)** — Compare the agent's generated diff against the gold diff using sequence matching.

Combined: `0.7 × test_score + 0.3 × patch_score`

## Task Schema

```json
{
  "instance_id": "django__django-12345",
  "repo": "django/django",
  "base_commit": "abc1234",
  "issue_title": "Fix the queryset bug",
  "issue_body": "When filtering with None...",
  "test_patch": "@@ -10,3 +10,3 @@",
  "gold_test_commands": ["pytest tests/test_qs.py -v"],
  "difficulty": "medium",
  "language": "python",
  "tags": ["bugfix"]
}
```

## AgentScope Integration

RepoEval pairs with [AgentScope](https://github.com/EmbrOS-Experimental/agent-scope):

1. **RepoEval** — "My agent passed 7/10 tasks"
2. **AgentScope** — "Here's exactly where it failed on task #3, step by step"

```bash
# Capture agent runs with AgentScope while RepoEval benchmarks them
pip install agentscope repoeval
```

## Troubleshooting

**"No bug-fix commits found"** — Your commits don't match the required patterns. Use `import-github` instead, or rename commits to include "Fix", "Bugfix", "Hotfix", or "Closes #".

**"Path does not exist"** — The previous command failed and didn't create the file. Run `repoeval validate` to check.

**GitHub API rate limit** — Set `GITHUB_TOKEN` env var: `$env:GITHUB_TOKEN="ghp_xxx"` (PowerShell) or `export GITHUB_TOKEN="ghp_xxx"` (bash).

## Built By

RepoEval is built by [EmbrOS](https://embros.xyz) — the AI Builder Operating System. Apache-2.0.

<div align="center">

**⭐ Star this repo if you think YOUR repo deserves its own benchmark**

[🐦 Twitter](https://x.com/embOS_ai) • [💬 Discord](https://discord.gg/FZsWkYpM9b) • [🌐 embros.xyz](https://embros.xyz)

</div>
