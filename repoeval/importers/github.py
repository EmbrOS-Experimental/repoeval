"""Task importers — GitHub issues, local git history, JSON/YAML files."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from typing import Any, Optional

from repoeval.core.models import Task


class JSONImporter:
    """Import tasks from a JSON or JSONL file."""

    @staticmethod
    def from_json(path: str | Path) -> list[Task]:
        """Import tasks from a JSON file (array of task objects)."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        if isinstance(data, list):
            return [Task.model_validate(t) for t in data]
        return [Task.model_validate(data)]

    @staticmethod
    def from_jsonl(path: str | Path) -> list[Task]:
        """Import tasks from a JSONL file (one task per line)."""
        tasks = []
        for line in Path(path).read_text(encoding="utf-8").strip().split("\n"):
            if line.strip():
                tasks.append(Task.model_validate_json(line))
        return tasks

    @staticmethod
    def from_swe_bench(path: str | Path) -> list[Task]:
        """Import from SWE-bench format JSON."""
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        tasks = []
        for item in data:
            task = Task(
                instance_id=item.get("instance_id", ""),
                repo=item.get("repo", ""),
                base_commit=item.get("base_commit", ""),
                issue_title=item.get("problem_statement", "")[:200],
                issue_body=item.get("problem_statement", ""),
                test_patch=item.get("test_patch", ""),
                gold_test_commands=item.get("FAIL_TO_PASS", []),
                language="python",
            )
            tasks.append(task)
        return tasks


class GitHistoryImporter:
    """Import tasks from local git history — find bug-fix commits."""

    BUG_FIX_PATTERNS = [
        r"fix(?:es|ed)?\s*#?(\d+)",
        r"bug(?:fix)?\s*:?\s*(.+)",
        r"hotfix\s*:?\s*(.+)",
        r"patch\s*:?\s*(.+)",
        r"resolve(?:s|d)?\s*#?(\d+)",
        r"close(?:s|d)?\s*#?(\d+)",
        r"repair(?:s|d)?\s*:?\s*(.+)",
    ]

    def __init__(self, repo_path: str | Path = "."):
        self.repo_path = Path(repo_path).resolve()

    def _run_git(self, args: list[str]) -> str:
        """Run a git command and return stdout."""
        result = subprocess.run(
            ["git", *args],
            cwd=self.repo_path,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip()

    def get_repo_name(self) -> str:
        """Get the repo name from remote URL or directory name."""
        try:
            url = self._run_git(["remote", "get-url", "origin"])
            # Extract owner/repo from URL
            match = re.search(r"[:/]([^/]+/[^/]+?)(?:\.git)?$", url)
            if match:
                return match.group(1)
        except Exception:
            pass
        return self.repo_path.name

    def find_bug_fix_commits(self, max_count: int = 50) -> list[dict[str, Any]]:
        """Find commits that look like bug fixes."""
        log_output = self._run_git([
            "log", "--oneline", "--no-merges",
            f"--max-count={max_count * 3}",  # Get more to filter
        ])

        bug_fixes = []
        for line in log_output.split("\n"):
            if not line.strip():
                continue
            parts = line.split(" ", 1)
            if len(parts) < 2:
                continue
            sha, message = parts[0], parts[1]

            # Check if message matches bug fix patterns
            is_bug_fix = False
            issue_ref = ""
            for pattern in self.BUG_FIX_PATTERNS:
                match = re.search(pattern, message, re.IGNORECASE)
                if match:
                    is_bug_fix = True
                    issue_ref = match.group(1) if match.groups() else ""
                    break

            if is_bug_fix:
                # Get the diff
                diff = self._run_git(["show", "--stat", sha])
                bug_fixes.append({
                    "sha": sha,
                    "message": message,
                    "issue_ref": issue_ref,
                    "diff_stat": diff,
                })

            if len(bug_fixes) >= max_count:
                break

        return bug_fixes

    def create_tasks_from_commits(
        self, max_count: int = 20
    ) -> list[Task]:
        """Create benchmark tasks from bug-fix commits."""
        commits = self.find_bug_fix_commits(max_count)
        repo_name = self.get_repo_name()
        tasks = []

        for commit in commits:
            # Get the parent commit (state before the fix)
            parent = self._run_git(["rev-parse", f"{commit['sha']}^"])
            
            # Get changed files
            changed_files = self._run_git([
                "diff", "--name-only", f"{parent}..{commit['sha']}"
            ])

            # Get the fix diff as test_patch
            fix_diff = self._run_git([
                "diff", f"{parent}..{commit['sha']}"
            ])

            task = Task(
                instance_id=commit["issue_ref"] or commit["sha"][:7],
                repo=str(self.repo_path),
                base_commit=parent,
                issue_title=commit["message"][:200],
                issue_body=commit["message"],
                test_patch=fix_diff,
                gold_test_commands=[],  # User must provide these
                difficulty="medium",
                tags=["git-history", "bug-fix"],
                metadata={
                    "fix_commit": commit["sha"],
                    "changed_files": changed_files,
                    "source": "git-history",
                },
            )
            tasks.append(task)

        return tasks


class GitHubImporter:
    """Import tasks from GitHub issues and PRs via API."""

    def __init__(self, token: Optional[str] = None):
        self.token = token

    def _headers(self) -> dict[str, str]:
        h = {"Accept": "application/vnd.github+json"}
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        return h

    def fetch_issues(
        self,
        owner: str,
        repo: str,
        state: str = "closed",
        labels: Optional[str] = None,
        max_count: int = 50,
    ) -> list[Task]:
        """Fetch closed issues from a GitHub repo and convert to tasks."""
        import httpx

        tasks = []
        url = f"https://api.github.com/repos/{owner}/{repo}/issues"
        params: dict[str, Any] = {
            "state": state,
            "per_page": min(max_count, 100),
            "page": 1,
        }
        if labels:
            params["labels"] = labels

        with httpx.Client(headers=self._headers(), timeout=30) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            issues = response.json()

            for issue in issues:
                # Skip pull requests (they have a pull_request key)
                if "pull_request" in issue:
                    continue

                task = Task(
                    instance_id=str(issue["number"]),
                    repo=f"{owner}/{repo}",
                    issue_title=issue.get("title", ""),
                    issue_body=issue.get("body", "") or "",
                    difficulty="medium",
                    tags=["github-issue"],
                    metadata={
                        "source": "github",
                        "url": issue.get("html_url", ""),
                        "labels": [l["name"] for l in issue.get("labels", [])],
                        "created_at": issue.get("created_at", ""),
                        "closed_at": issue.get("closed_at", ""),
                    },
                )
                tasks.append(task)

                if len(tasks) >= max_count:
                    break

        return tasks

    def fetch_issue_with_comments(
        self,
        owner: str,
        repo: str,
        issue_number: int,
    ) -> Task:
        """Fetch a single issue with full body and comments."""
        import httpx

        url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}"
        with httpx.Client(headers=self._headers(), timeout=30) as client:
            response = client.get(url)
            response.raise_for_status()
            issue = response.json()

        return Task(
            instance_id=str(issue["number"]),
            repo=f"{owner}/{repo}",
            issue_title=issue.get("title", ""),
            issue_body=issue.get("body", "") or "",
            difficulty="medium",
            tags=["github-issue"],
            metadata={
                "source": "github",
                "url": issue.get("html_url", ""),
                "labels": [l["name"] for l in issue.get("labels", [])],
            },
        )
