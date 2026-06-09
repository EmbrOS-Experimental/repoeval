# Contributing to RepoEval

```bash
git clone https://github.com/EmbrOS-Experimental/repoeval.git
cd repoeval
pip install -e ".[dev]"
python3 -m pytest tests/ -v
```

32 tests must pass before submitting a PR.

## Project Structure

```
repoeval/
├── core/models.py         # Task, BenchmarkRun, TaskResult
├── importers/github.py    # GitHub importer, Git history importer, JSON
├── executors/runner.py    # Shell agent, Aider agent, local executor
├── scorers/patch.py       # Patch scorer, test scorer, composite
├── scorers/leaderboard.py # HTML + JSON leaderboard generator
└── cli/main.py            # CLI: run, import, report, compare
```
