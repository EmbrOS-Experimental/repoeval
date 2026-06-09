"""Shared fixtures."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from repoeval.core.models import BenchmarkRun, Task, TaskResult, TaskStatus
from repoeval.importers.github import GitHistoryImporter, JSONImporter
from repoeval.executors.runner import LocalTaskExecutor, ShellAgentRunner
from repoeval.scorers.patch import CompositeScorer, PatchScorer, TestScorer
from repoeval.scorers.leaderboard import LeaderboardGenerator


@pytest.fixture
def sample_task() -> Task:
    return Task(
        id="test-001",
        instance_id="42",
        repo="owner/repo",
        base_commit="abc1234",
        issue_title="Fix login bug",
        issue_body="Users cannot login when token is null",
        test_patch="@@ -10,3 +10,3 @@\n-    token.decode()\n+    token.decode() if token else None",
        gold_test_commands=["pytest tests/test_auth.py -v"],
        difficulty="medium",
        language="python",
        tags=["bugfix", "auth"],
    )


@pytest.fixture
def sample_tasks(sample_task) -> list[Task]:
    tasks = [sample_task]
    for i in range(2, 6):
        t = sample_task.model_copy()
        t.id = f"test-{i:03d}"
        t.instance_id = str(40 + i)
        t.issue_title = f"Bug fix #{i}"
        tasks.append(t)
    return tasks


@pytest.fixture
def sample_tasks_file(sample_tasks, tmp_path) -> Path:
    path = tmp_path / "tasks.json"
    with open(path, "w") as f:
        json.dump([t.model_dump(mode="json") for t in sample_tasks], f, default=str)
    return path


@pytest.fixture
def completed_benchmark(sample_tasks) -> BenchmarkRun:
    bench = BenchmarkRun(
        name="Test Benchmark",
        agent_type="shell",
        model="test-model",
        tasks=sample_tasks,
    )
    for i, task in enumerate(sample_tasks):
        result = TaskResult(
            task_id=task.id,
            task=task,
            agent_type="shell",
            model="test-model",
            status=TaskStatus.PASSED if i < 3 else TaskStatus.FAILED,
            duration_ms=1000.0,
            tokens_used=500,
            cost_usd=0.01,
            tests_passed=3 if i < 3 else 1,
            tests_failed=0 if i < 3 else 2,
            tests_total=3,
        )
        bench.add_result(result)
    bench.finalize()
    return bench


@pytest.fixture
def tmp_output(tmp_path) -> Path:
    return tmp_path / "output"
