from skillablate.core import (
    grade_output,
    grade_task,
    summarize,
)


def test_exact_grader():
    grader = {
        "type": "exact",
        "expected": "PASS",
    }

    assert grade_output("PASS", grader) == 1.0
    assert grade_output("FAIL", grader) == 0.0


def test_regex_grader():
    grader = {
        "type": "regex",
        "pattern": r"P[0-3]",
    }

    assert grade_output("severity=P2", grader) == 1.0
    assert grade_output("unknown", grader) == 0.0


def test_json_equals_grader():
    grader = {
        "type": "json_equals",
        "path": "severity",
        "expected": "P0",
    }

    assert (
        grade_output('{"severity":"P0"}', grader)
        == 1.0
    )

    assert (
        grade_output('{"severity":"P1"}', grader)
        == 0.0
    )


def test_invalid_json_fails_cleanly():
    grader = {
        "type": "json_equals",
        "path": "severity",
        "expected": "P0",
    }

    assert grade_output("not json", grader) == 0.0


def test_weighted_task_score():
    graders = [
        {
            "type": "json_equals",
            "path": "severity",
            "expected": "P0",
            "weight": 0.8,
        },
        {
            "type": "regex",
            "pattern": "database",
            "weight": 0.2,
        },
    ]

    score, details = grade_task(
        '{"severity":"P0","reason":"database"}',
        graders,
    )

    assert score == 1.0
    assert len(details) == 2


def test_summary_delta():
    result = {
        "records": [
            {
                "condition": "baseline",
                "score": 0.5,
            },
            {
                "condition": "baseline",
                "score": 0.5,
            },
            {
                "condition": "skill",
                "score": 1.0,
            },
            {
                "condition": "skill",
                "score": 0.8,
            },
        ]
    }

    summary = summarize(result)

    assert summary["baseline"] == 0.5
    assert summary["skill"] == 0.9
    assert summary["delta"] == 0.4
