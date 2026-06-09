"""Tests for core models."""

from __future__ import annotations

from repoeval.core.models import (
    AgentType,
    BenchmarkRun,
    LeaderboardEntry,
    Task,
    TaskResult,
    TaskStatus,
)


def test_task_creation():
    task = Task(
        id="t1",
        issue_title="Fix bug",
        issue_body="Something is broken",
    )
    assert task.id == "t1"
    assert task.difficulty == "medium"
    assert task.difficulty == "medium"
    assert task.language == "python"


def test_task_result_creation():
    result = TaskResult(
        task_id="t1",
        status=TaskStatus.PASSED,
        duration_ms=1500.0,
        tokens_used=1000,
        cost_usd=0.03,
    )
    assert result.status == TaskStatus.PASSED
    assert result.duration_ms == 1500.0
    assert result.tests_passed == 0
    assert result.patch_correct is None


def test_benchmark_run_add_result():
    bench = BenchmarkRun(name="test", agent_type="shell")
    
    r1 = TaskResult(task_id="t1", status=TaskStatus.PASSED, duration_ms=1000)
    bench.add_result(r1)
    assert bench.total_tasks == 1
    assert bench.passed == 1
    assert bench.pass_rate == 1.0

    r2 = TaskResult(task_id="t2", status=TaskStatus.FAILED, duration_ms=2000)
    bench.add_result(r2)
    assert bench.total_tasks == 2
    assert bench.passed == 1
    assert bench.failed == 1
    assert bench.pass_rate == 0.5
    assert bench.total_duration_ms == 3000


def test_benchmark_run_finalize():
    bench = BenchmarkRun(name="test")
    bench.finalize()
    assert bench.completed_at is not None


def test_benchmark_run_error_counting():
    bench = BenchmarkRun(name="test")
    bench.add_result(TaskResult(task_id="t1", status=TaskStatus.ERROR))
    bench.add_result(TaskResult(task_id="t2", status=TaskStatus.PASSED))
    assert bench.errors == 1
    assert bench.passed == 1


def test_leaderboard_entry():
    entry = LeaderboardEntry(
        run_id="run-1",
        name="Claude vs Codex",
        agent_type="aider",
        model="claude-sonnet-4",
        total_tasks=10,
        passed=7,
        pass_rate=0.7,
    )
    assert entry.pass_rate == 0.7
    assert entry.model == "claude-sonnet-4"


def test_task_status_enum():
    assert TaskStatus.PASSED.value == "passed"
    assert TaskStatus.FAILED.value == "failed"
    assert TaskStatus.ERROR.value == "error"


def test_agent_type_enum():
    assert AgentType.AIDER.value == "aider"
    assert AgentType.SHELL.value == "shell"
