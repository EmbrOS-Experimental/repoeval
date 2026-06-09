"""Tests for scorers."""

from __future__ import annotations

from repoeval.core.models import Task, TaskResult, TaskStatus
from repoeval.scorers.patch import CompositeScorer, PatchScorer, TestScorer


def test_patch_scorer_identical():
    patch = "+line1\n+line2\n-line3"
    score = PatchScorer.score(patch, patch)
    assert score == 1.0


def test_patch_scorer_completely_different():
    gold = "+fix the bug\n-remove old code"
    generated = "+add new feature\n-remove something else"
    score = PatchScorer.score(gold, generated)
    assert score < 0.5


def test_patch_scorer_partial_match():
    gold = "+token.decode() if token else None\n-remove old line"
    generated = "+token.decode() if token else None\n-different removal"
    score = PatchScorer.score(gold, generated)
    assert 0.3 < score < 1.0


def test_patch_scorer_empty():
    assert PatchScorer.score("", "something") == 0.0
    assert PatchScorer.score("something", "") == 0.0
    assert PatchScorer.score("", "") == 0.0


def test_patch_scorer_is_correct():
    gold = "+token.decode() if token else None"
    good = "+token.decode() if token else None"
    bad = "+completely different fix"
    
    assert PatchScorer.is_correct(gold, good, threshold=0.8) is True
    assert PatchScorer.is_correct(gold, bad, threshold=0.8) is False


def test_test_scorer_parse_pytest_output():
    scorer = TestScorer(".")
    
    output = "5 passed, 2 failed in 0.3s"
    passed, failed = scorer._parse_test_output(output)
    assert passed == 5
    assert failed == 2


def test_test_scorer_parse_ok():
    scorer = TestScorer(".")
    
    output = "3 passed in 0.1s\nOK"
    passed, failed = scorer._parse_test_output(output)
    assert passed == 3
    assert failed == 0


def test_test_scorer_parse_failure():
    scorer = TestScorer(".")
    
    output = "1 failed, 2 passed"
    passed, failed = scorer._parse_test_output(output)
    assert passed == 2
    assert failed == 1


def test_composite_scorer_passed_result(sample_task):
    scorer = CompositeScorer()
    result = TaskResult(
        task_id=sample_task.id,
        task=sample_task,
        status=TaskStatus.RUNNING,
        tests_passed=3,
        tests_failed=0,
        tests_total=3,
    )
    
    scored = scorer.score_result(result, gold_patch="+fix", test_commands=[])
    assert scored.status == TaskStatus.PASSED


def test_composite_scorer_failed_result(sample_task):
    scorer = CompositeScorer()
    result = TaskResult(
        task_id=sample_task.id,
        task=sample_task,
        status=TaskStatus.RUNNING,
        tests_passed=1,
        tests_failed=2,
        tests_total=3,
    )
    
    scored = scorer.score_result(result, gold_patch="+fix", test_commands=[])
    assert scored.status == TaskStatus.FAILED


def test_leaderboard_generator(completed_benchmark, tmp_output):
    from repoeval.scorers.leaderboard import LeaderboardGenerator
    
    gen = LeaderboardGenerator()
    html_path = gen.generate(completed_benchmark, output_dir=tmp_output)
    
    assert html_path.exists()
    html_content = html_path.read_text()
    assert "Test Benchmark" in html_content
    assert "60.0%" in html_content or "3/5" in html_content
    
    # Check JSON was also generated
    json_path = tmp_output / "results.json"
    assert json_path.exists()


def test_leaderboard_comparison(completed_benchmark, tmp_output):
    from repoeval.scorers.leaderboard import LeaderboardGenerator
    
    run2 = completed_benchmark.model_copy()
    run2.id = "run-2"
    run2.name = "Run 2"
    run2.pass_rate = 0.8
    
    gen = LeaderboardGenerator()
    html_path = gen.generate_comparison(
        [completed_benchmark, run2],
        output_dir=tmp_output,
        title="Model Comparison",
    )
    
    assert html_path.exists()
    content = html_path.read_text()
    assert "Model Comparison" in content
