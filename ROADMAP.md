# RepoEval — Roadmap

## Priority Score: 90/100
Impact: 4.5 | Novelty: 4.5 | Virality: 5.0

### Month 1: Task Pipeline
- [ ] Task importer (GitHub issues API + manual JSON)
- [ ] Standardized task schema
- [ ] Docker execution harness

### Month 1–2: Agents & Scoring
- [ ] Two agent adapters (Aider, OpenHands)
- [ ] Scoring engine (pass/fail, patch correctness)
- [ ] Static HTML dashboard

### Month 2–3: CI & Scale
- [ ] CI integration (GitHub Actions)
- [ ] Holdout task system
- [ ] Multi-model comparison mode

## Effort
- Solo MVP: 2–3 PM
- Team of 3: 4–5 PM (~4–6 weeks elapsed)

## Demo Plan
1. Import 20 real issues from a popular OSS repo
2. Run Claude/Codex/Gemini on all 20
3. Publish leaderboard as GitHub Pages
4. Post thread: "Which AI agent is best at fixing real bugs in [project]?"
