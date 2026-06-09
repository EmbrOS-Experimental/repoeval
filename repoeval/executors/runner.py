"""Task execution engine — run agents against benchmark tasks."""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any, Callable, Optional

from repoeval.core.models import AgentType, Task, TaskResult, TaskStatus

import logging

logger = logging.getLogger(__name__)


class AgentRunner:
    """Base class for agent runners."""

    def run(self, task: Task, work_dir: str | Path) -> TaskResult:
        """Execute the agent on a task and return the result."""
        raise NotImplementedError


class ShellAgentRunner(AgentRunner):
    """Run a custom shell command as the agent."""

    def __init__(
        self,
        command: list[str],
        timeout: float = 300.0,
        env: Optional[dict[str, str]] = None,
    ):
        self.command = command
        self.timeout = timeout
        self.env = env or {}

    def run(self, task: Task, work_dir: str | Path) -> TaskResult:
        result = TaskResult(
            task_id=task.id,
            task=task,
            agent_type="shell",
            status=TaskStatus.RUNNING,
            started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )

        start = time.monotonic()
        try:
            # Build command with substitutions
            cmd = []
            for part in self.command:
                part = part.replace("{issue}", task.issue_body)
                part = part.replace("{title}", task.issue_title)
                part = str(work_dir).join(part.split("{work_dir}"))
                cmd.append(part)

            logger.info(f"Running: {' '.join(cmd)}")

            proc = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env={**os.environ, **self.env},
            )

            duration = (time.monotonic() - start) * 1000
            result.duration_ms = duration
            result.agent_output = proc.stdout[-10000:]  # Last 10K chars
            result.status = TaskStatus.PASSED if proc.returncode == 0 else TaskStatus.FAILED

            if proc.returncode != 0:
                result.error = proc.stderr[-2000:]

        except subprocess.TimeoutExpired:
            result.status = TaskStatus.ERROR
            result.error = f"Timed out after {self.timeout}s"
            result.duration_ms = (time.monotonic() - start) * 1000
        except Exception as e:
            result.status = TaskStatus.ERROR
            result.error = str(e)
            result.duration_ms = (time.monotonic() - start) * 1000

        result.completed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        return result


class AiderAgentRunner(AgentRunner):
    """Run Aider as the agent."""

    def __init__(
        self,
        model: str = "claude-sonnet-4",
        timeout: float = 600.0,
        api_key: Optional[str] = None,
    ):
        self.model = model
        self.timeout = timeout
        self.api_key = api_key

    def run(self, task: Task, work_dir: str | Path) -> TaskResult:
        result = TaskResult(
            task_id=task.id,
            task=task,
            agent_type="aider",
            model=self.model,
            status=TaskStatus.RUNNING,
            started_at=__import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        )

        start = time.monotonic()
        try:
            env = dict(os.environ)
            if self.api_key:
                env["OPENAI_API_KEY"] = self.api_key

            cmd = [
                "aider",
                "--model", self.model,
                "--no-git",
                "--yes",
                "--message", f"{task.issue_title}\n\n{task.issue_body}",
            ]

            proc = subprocess.run(
                cmd,
                cwd=work_dir,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                env=env,
            )

            duration = (time.monotonic() - start) * 1000
            result.duration_ms = duration
            result.agent_output = proc.stdout[-10000:]
            result.status = TaskStatus.PASSED if proc.returncode == 0 else TaskStatus.FAILED

            # Try to extract token usage from aider output
            self._parse_token_usage(result, proc.stdout)

        except subprocess.TimeoutExpired:
            result.status = TaskStatus.ERROR
            result.error = f"Aider timed out after {self.timeout}s"
            result.duration_ms = self.timeout * 1000
        except FileNotFoundError:
            result.status = TaskStatus.ERROR
            result.error = "aider not found. Install with: pip install aider-chat"
        except Exception as e:
            result.status = TaskStatus.ERROR
            result.error = str(e)

        result.completed_at = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
        return result

    def _parse_token_usage(self, result: TaskResult, output: str) -> None:
        """Try to parse token usage from Aider output."""
        import re
        # Aider outputs token usage like: "Tokens: 1,234 sent, 567 received"
        match = re.search(r"Tokens?:\s*([\d,]+)\s*sent,\s*([\d,]+)\s*received", output)
        if match:
            sent = int(match.group(1).replace(",", ""))
            received = int(match.group(2).replace(",", ""))
            result.tokens_used = sent + received


class LocalTaskExecutor:
    """Execute tasks locally (no Docker) — checkout, run agent, score."""

    def __init__(
        self,
        runner: AgentRunner,
        work_base_dir: Optional[str | Path] = None,
        cleanup: bool = True,
    ):
        self.runner = runner
        self.work_base_dir = Path(work_base_dir) if work_base_dir else Path(tempfile.gettempdir()) / "repoeval"
        self.cleanup = cleanup

    def _prepare_work_dir(self, task: Task) -> Path:
        """Clone/checkout the repo at the right commit."""
        work_dir = self.work_base_dir / task.id
        
        if isinstance(task.repo, str) and "/" in task.repo and not Path(task.repo).exists():
            # It's a GitHub repo reference — clone it
            if work_dir.exists():
                shutil.rmtree(work_dir)
            subprocess.run(
                ["git", "clone", f"https://github.com/{task.repo}.git", str(work_dir)],
                capture_output=True, timeout=120,
            )
        elif Path(task.repo).exists():
            # It's a local repo — copy it
            if work_dir.exists():
                shutil.rmtree(work_dir)
            shutil.copytree(task.repo, work_dir)
        else:
            # Create empty work dir
            work_dir.mkdir(parents=True, exist_ok=True)

        # Checkout the base commit if specified
        if task.base_commit:
            subprocess.run(
                ["git", "checkout", task.base_commit],
                cwd=work_dir,
                capture_output=True,
                timeout=30,
            )

        return work_dir

    def execute_task(self, task: Task) -> TaskResult:
        """Execute a single task."""
        logger.info(f"Executing task {task.id}: {task.issue_title[:60]}")
        
        try:
            work_dir = self._prepare_work_dir(task)
            result = self.runner.run(task, work_dir)
            
            if self.cleanup:
                self._cleanup_work_dir(work_dir)
            
            return result
        except Exception as e:
            return TaskResult(
                task_id=task.id,
                task=task,
                agent_type=self.runner.__class__.__name__,
                status=TaskStatus.ERROR,
                error=str(e),
            )

    def _cleanup_work_dir(self, work_dir: Path) -> None:
        try:
            if work_dir.exists():
                shutil.rmtree(work_dir)
        except Exception:
            pass

    def execute_all(
        self,
        tasks: list[Task],
        callback: Optional[Callable[[Task, TaskResult], None]] = None,
    ) -> list[TaskResult]:
        """Execute all tasks sequentially."""
        results = []
        for i, task in enumerate(tasks):
            logger.info(f"Task {i+1}/{len(tasks)}")
            result = self.execute_task(task)
            results.append(result)
            if callback:
                callback(task, result)
        return results
