"""Scorers — evaluate task results."""

from __future__ import annotations

import difflib
import re
import subprocess
from pathlib import Path
from typing import Optional

from repoeval.core.models import Task, TaskResult, TaskStatus

import logging

logger = logging.getLogger(__name__)


class PatchScorer:
    """Score patch correctness by comparing generated vs gold patch."""

    @staticmethod
    def score(gold_patch: str, generated_patch: str) -> float:
        """Return similarity score 0.0-1.0 between two patches."""
        if not gold_patch.strip() or not generated_patch.strip():
            return 0.0

        # Normalize: remove diff headers, keep only actual changes
        gold_lines = PatchScorer._extract_changed_lines(gold_patch)
        gen_lines = PatchScorer._extract_changed_lines(generated_patch)

        if not gold_lines:
            return 0.0

        # Use difflib sequence matcher
        matcher = difflib.SequenceMatcher(None, gold_lines, gen_lines)
        return matcher.ratio()

    @staticmethod
    def _extract_changed_lines(patch: str) -> list[str]:
        """Extract only the actual changed lines from a diff."""
        lines = []
        for line in patch.split("\n"):
            # Keep added (+) and removed (-) lines, skip headers
            if line.startswith("+") and not line.startswith("+++"):
                lines.append(line[1:].strip())
            elif line.startswith("-") and not line.startswith("---"):
                lines.append(line[1:].strip())
        return lines

    @staticmethod
    def is_correct(gold_patch: str, generated_patch: str, threshold: float = 0.8) -> bool:
        """Check if generated patch is correct enough."""
        return PatchScorer.score(gold_patch, generated_patch) >= threshold


class TestScorer:
    """Run gold tests and check pass/fail."""

    def __init__(self, work_dir: str | Path, timeout: float = 120.0):
        self.work_dir = Path(work_dir)
        self.timeout = timeout

    def run_tests(self, test_commands: list[str]) -> tuple[int, int, str]:
        """Run test commands and return (passed, failed, output)."""
        total_passed = 0
        total_failed = 0
        all_output = []

        for cmd in test_commands:
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=self.work_dir,
                    capture_output=True,
                    text=True,
                    timeout=self.timeout,
                )
                output = result.stdout + result.stderr
                all_output.append(f"$ {cmd}\n{output}")

                # Parse common test output patterns
                passed, failed = self._parse_test_output(output)
                total_passed += passed
                total_failed += failed

            except subprocess.TimeoutExpired:
                all_output.append(f"$ {cmd}\n[TIMEOUT]")
                total_failed += 1
            except Exception as e:
                all_output.append(f"$ {cmd}\n[ERROR: {e}]")
                total_failed += 1

        return total_passed, total_failed, "\n".join(all_output)

    def _parse_test_output(self, output: str) -> tuple[int, int]:
        """Parse test output to extract pass/fail counts."""
        passed = 0
        failed = 0

        # pytest pattern: "5 passed, 2 failed" or "5 passed"
        match = re.search(r"(\d+)\s*passed", output)
        if match:
            passed = int(match.group(1))
        match = re.search(r"(\d+)\s*failed", output)
        if match:
            failed = int(match.group(1))

        # If no pattern matched, check exit code indicators
        if passed == 0 and failed == 0:
            if "OK" in output or "SUCCESS" in output:
                passed = 1
            elif "FAIL" in output or "ERROR" in output:
                failed = 1

        return passed, failed


class CompositeScorer:
    """Combine patch and test scoring."""

    def __init__(self, patch_weight: float = 0.3, test_weight: float = 0.7):
        self.patch_weight = patch_weight
        self.test_weight = test_weight
        self.patch_scorer = PatchScorer()

    def score_result(
        self,
        result: TaskResult,
        gold_patch: str = "",
        test_commands: Optional[list[str]] = None,
        work_dir: Optional[str | Path] = None,
    ) -> TaskResult:
        """Score a task result and update it."""
        scores = []

        # Patch score
        if gold_patch and result.agent_output:
            patch_score = self.patch_scorer.score(gold_patch, result.agent_output)
            result.patch_correct = patch_score >= 0.8
            scores.append(("patch", patch_score))

        # Test score
        if test_commands and work_dir:
            test_scorer = TestScorer(work_dir)
            passed, failed, output = test_scorer.run_tests(test_commands)
            result.tests_passed = passed
            result.tests_failed = failed
            result.tests_total = passed + failed
            result.test_output = output

            if passed + failed > 0:
                test_score = passed / (passed + failed)
            else:
                test_score = 0.0
            scores.append(("test", test_score))

        # Determine final status
        if result.status == TaskStatus.ERROR:
            pass
        elif result.tests_total > 0 and result.tests_passed == result.tests_total:
            result.status = TaskStatus.PASSED
        elif result.patch_correct:
            result.status = TaskStatus.PASSED
        elif result.tests_total > 0 and result.tests_failed > 0:
            result.status = TaskStatus.FAILED

        return result
