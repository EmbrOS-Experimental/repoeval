"""Tests for execution engine."""

from __future__ import annotations

from repoeval.core.models import Task, TaskResult, TaskStatus
from repoeval.executors.runner import LocalTaskExecutor, ShellAgentRunner


import os
import sys


def _echo_cmd(text: str) -> list[str]:
    """Cross-platform echo command."""
    if sys.platform == "win32":
        return ["cmd", "/c", "echo", text]
    return ["echo", text]


def _false_cmd() -> list[str]:
    """Cross-platform false command."""
    return [sys.executable, "-c", "exit(1)"]


def test_shell_runner_success(sample_task, tmp_path):
    runner = ShellAgentRunner(command=_echo_cmd("hello"))
    result = runner.run(sample_task, tmp_path)
    
    assert result.status == TaskStatus.PASSED
    assert result.task_id == sample_task.id
    assert "hello" in result.agent_output
    assert result.duration_ms > 0


def test_shell_runner_failure(sample_task, tmp_path):
    runner = ShellAgentRunner(command=_false_cmd())
    result = runner.run(sample_task, tmp_path)
    
    assert result.status == TaskStatus.FAILED


def _sleep_cmd(seconds: str) -> list[str]:
    """Cross-platform sleep command."""
    return [sys.executable, "-c", f"import time; time.sleep({seconds})"]


def test_shell_runner_timeout(sample_task, tmp_path):
    runner = ShellAgentRunner(command=_sleep_cmd("10"), timeout=0.5)
    result = runner.run(sample_task, tmp_path)
    
    assert result.status == TaskStatus.ERROR
    assert "timed out" in result.error.lower()


def test_shell_runner_with_issue_substitution(sample_task, tmp_path):
    if sys.platform == "win32":
        runner = ShellAgentRunner(command=["cmd", "/c", "echo", "{issue}"])
    else:
        runner = ShellAgentRunner(command=["echo", "{issue}"])
    result = runner.run(sample_task, tmp_path)
    
    assert result.status == TaskStatus.PASSED
    assert "token is null" in result.agent_output


def test_local_executor(sample_task, tmp_path):
    # Use a local directory as the repo (not a GitHub URL)
    local_repo = tmp_path / "local_repo"
    local_repo.mkdir()
    (local_repo / "main.py").write_text("print('hello')")
    
    task = sample_task.model_copy()
    task.repo = str(local_repo)
    task.base_commit = ""  # Don't try to checkout
    
    runner = ShellAgentRunner(command=_echo_cmd("test"))
    executor = LocalTaskExecutor(runner, work_base_dir=tmp_path / "work", cleanup=True)
    
    result = executor.execute_task(task)
    assert result.status == TaskStatus.PASSED


def test_local_executor_multiple_tasks(sample_tasks, tmp_path):
    # Use a local directory as the repo
    local_repo = tmp_path / "local_repo"
    local_repo.mkdir()
    (local_repo / "main.py").write_text("print('hello')")
    
    for task in sample_tasks:
        task.repo = str(local_repo)
        task.base_commit = ""
    
    runner = ShellAgentRunner(command=_echo_cmd("ok"))
    executor = LocalTaskExecutor(runner, work_base_dir=tmp_path / "work", cleanup=True)
    
    results = executor.execute_all(sample_tasks)
    assert len(results) == len(sample_tasks)
    assert all(r.status == TaskStatus.PASSED for r in results)


def test_local_executor_callback(sample_task, tmp_path):
    local_repo = tmp_path / "local_repo"
    local_repo.mkdir()
    
    task = sample_task.model_copy()
    task.repo = str(local_repo)
    task.base_commit = ""
    
    runner = ShellAgentRunner(command=_echo_cmd("ok"))
    executor = LocalTaskExecutor(runner, work_base_dir=tmp_path / "work", cleanup=True)
    
    callbacks = []
    def on_complete(task, result):
        callbacks.append((task.id, result.status))
    
    executor.execute_all([task], callback=on_complete)
    assert len(callbacks) == 1
    assert callbacks[0][0] == task.id
