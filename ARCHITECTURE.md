# RepoEval — Architecture

## Stack
- **Language**: Python (ecosystem fit: SWE-bench, Docker SDK, GitHub API)
- **Task Schema**: SWE-bench-style JSON
- **Execution**: Docker containers (reproducible, isolated)
- **Scoring**: Reuse Inspect AI / OpenAI Evals patterns
- **Reporting**: Static HTML dashboard + JSON artifacts
- **Deployment**: Local CLI first, CI integration, cloud for shared leaderboards

## Data Flow
```
Repo (git/issues) → Task Importer → Task Schema (JSON)
                                        ↓
                              Agent/Model Adapters
                                        ↓
                              Docker Execution
                                        ↓
                              Scoring Engine
                                        ↓
                        Leaderboard (HTML + JSON)
```

## MVP Scope (2–3 PM solo, 4–5 PM team of 3)
1. Task importer (GitHub issues + manual curation)
2. Two agent adapters (e.g., Aider + OpenHands)
3. Docker execution harness
4. Static leaderboard HTML + CI JSON output

## Task Schema (SWE-bench-style)
```json
{
  "task_id": "repo-123",
  "problem_statement": "...",
  "base_commit": "abc123",
  "setup_commands": ["npm install"],
  "test_commands": ["npm test"],
  "expected_files_changed": ["src/auth.ts"],
  "difficulty": "medium",
  "category": "bug-fix"
}
```

## Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Secret leakage in containers | No network access by default, volume mounts for secrets |
| Benchmark gaming | Holdout task sets, strict dataset versioning |
| Cost blowout | Cached environments, configurable run budgets |
| Aggregate scores misleading | Always preserve task-level evidence |
