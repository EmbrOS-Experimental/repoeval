"""Core data models for RepoEval — task schema, benchmark runs, results."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import Any, Optional

from pydantic import BaseModel, Field


class TaskStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    ERROR = "error"
    SKIPPED = "skipped"


class AgentType(str, enum.Enum):
    AIDER = "aider"
    CUSTOM = "custom"
    SHELL = "shell"


class Task(BaseModel):
    """A single benchmark task — SWE-bench style."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    instance_id: str = ""  # original issue/PR number
    repo: str = ""  # "owner/repo" or local path
    base_commit: str = ""
    issue_title: str = ""
    issue_body: str = ""
    test_patch: str = ""  # gold patch that fixes the issue
    gold_test_commands: list[str] = Field(default_factory=list)  # tests that should pass after fix
    difficulty: str = "medium"  # easy, medium, hard
    language: str = "python"
    tags: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class TaskResult(BaseModel):
    """Result of running a single task."""
    task_id: str
    task: Optional[Task] = None
    status: TaskStatus = TaskStatus.PENDING
    agent_type: str = "custom"
    model: str = "unknown"
    
    # Execution
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # Patch
    generated_patch: str = ""
    patch_correct: Optional[bool] = None  # None = not yet scored
    
    # Tests
    tests_passed: int = 0
    tests_failed: int = 0
    tests_total: int = 0
    test_output: str = ""
    
    # Cost
    tokens_used: int = 0
    cost_usd: float = 0.0
    
    # Agent output
    agent_output: str = ""
    agent_trace_path: str = ""  # link to AgentScope trace if available
    
    error: Optional[str] = None


class BenchmarkRun(BaseModel):
    """A complete benchmark run across multiple tasks."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:12])
    name: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    
    # Config
    agent_type: str = "custom"
    model: str = "unknown"
    tasks: list[Task] = Field(default_factory=list)
    results: list[TaskResult] = Field(default_factory=list)
    
    # Summary
    total_tasks: int = 0
    passed: int = 0
    failed: int = 0
    errors: int = 0
    pass_rate: float = 0.0
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    
    metadata: dict[str, Any] = Field(default_factory=dict)

    def add_result(self, result: TaskResult) -> None:
        """Add a task result and update summary."""
        self.results.append(result)
        self.total_tasks = len(self.results)
        
        if result.status == TaskStatus.PASSED:
            self.passed += 1
        elif result.status == TaskStatus.FAILED:
            self.failed += 1
        elif result.status == TaskStatus.ERROR:
            self.errors += 1
        
        self.total_duration_ms += result.duration_ms
        self.total_tokens += result.tokens_used
        self.total_cost_usd += result.cost_usd
        
        completed = self.passed + self.failed
        if completed > 0:
            self.pass_rate = self.passed / completed

    def finalize(self) -> None:
        self.completed_at = datetime.now(timezone.utc)


class LeaderboardEntry(BaseModel):
    """A single entry on the leaderboard."""
    run_id: str
    name: str
    agent_type: str
    model: str
    total_tasks: int = 0
    passed: int = 0
    failed: int = 0
    pass_rate: float = 0.0
    total_duration_ms: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
