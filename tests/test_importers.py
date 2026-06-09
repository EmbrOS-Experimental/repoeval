"""Tests for importers."""

from __future__ import annotations

import json
from pathlib import Path

from repoeval.importers.github import GitHistoryImporter, JSONImporter


def test_json_importer(sample_tasks_file):
    tasks = JSONImporter.from_json(sample_tasks_file)
    assert len(tasks) == 5
    assert tasks[0].id == "test-001"
    assert tasks[0].issue_title == "Fix login bug"


def test_json_importer_single_task(tmp_path):
    task = {"id": "single", "issue_title": "One task"}
    path = tmp_path / "single.json"
    path.write_text(json.dumps(task))
    
    tasks = JSONImporter.from_json(path)
    assert len(tasks) == 1
    assert tasks[0].id == "single"


def test_jsonl_importer(sample_tasks, tmp_path):
    path = tmp_path / "tasks.jsonl"
    with open(path, "w") as f:
        for task in sample_tasks:
            f.write(task.model_dump_json() + "\n")
    
    tasks = JSONImporter.from_jsonl(path)
    assert len(tasks) == 5


def test_swe_bench_importer(tmp_path):
    """Test importing from SWE-bench format."""
    data = [
        {
            "instance_id": "django__django-12345",
            "repo": "django/django",
            "base_commit": "abc123",
            "problem_statement": "Fix the queryset bug",
            "test_patch": "@@ -10,3 +10,3 @@\n-old\n+new",
            "FAIL_TO_PASS": ["tests/test_qs.py::test_filter"],
        }
    ]
    path = tmp_path / "swe_bench.json"
    path.write_text(json.dumps(data))
    
    tasks = JSONImporter.from_swe_bench(path)
    assert len(tasks) == 1
    assert tasks[0].instance_id == "django__django-12345"
    assert tasks[0].repo == "django/django"
    assert len(tasks[0].gold_test_commands) == 1


def test_git_history_importer_patterns():
    """Test that bug-fix commit patterns are recognized."""
    importer = GitHistoryImporter(".")
    
    # These should match
    assert any(
        __import__("re").search(p, "Fix #123: login bug", __import__("re").IGNORECASE)
        for p in importer.BUG_FIX_PATTERNS
    )
    assert any(
        __import__("re").search(p, "Bugfix: resolve null pointer", __import__("re").IGNORECASE)
        for p in importer.BUG_FIX_PATTERNS
    )
    assert any(
        __import__("re").search(p, "Hotfix: critical security issue", __import__("re").IGNORECASE)
        for p in importer.BUG_FIX_PATTERNS
    )
    assert any(
        __import__("re").search(p, "Closes #456", __import__("re").IGNORECASE)
        for p in importer.BUG_FIX_PATTERNS
    )
