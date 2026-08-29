from __future__ import annotations

import json
import os
import re
import shlex
import statistics
import subprocess
from pathlib import Path
from typing import Any

import yaml


class SkillAblateError(Exception):
    """Base exception for SkillAblate."""


def load_suite(path: str | Path) -> dict[str, Any]:
    path = Path(path)

    if not path.exists():
        raise SkillAblateError(f"Benchmark file does not exist: {path}")

    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)

    if not isinstance(data, dict):
        raise SkillAblateError("Benchmark root must be a mapping.")

    if data.get("schema_version") != "0.1":
        raise SkillAblateError(
            "Unsupported or missing schema_version. Expected '0.1'."
        )

    if not isinstance(data.get("suite"), dict):
        raise SkillAblateError("Benchmark must contain a suite mapping.")

    tasks = data.get("tasks")

    if not isinstance(tasks, list) or not tasks:
        raise SkillAblateError(
            "Benchmark must contain at least one task."
        )

    for task in tasks:
        if not isinstance(task, dict):
            raise SkillAblateError("Each task must be a mapping.")

        if not task.get("id"):
            raise SkillAblateError("Every task requires an id.")

        if not isinstance(task.get("prompt"), str):
            raise SkillAblateError(
                f"Task {task.get('id')} requires a prompt."
            )

        graders = task.get("graders")

        if not isinstance(graders, list) or not graders:
            raise SkillAblateError(
                f"Task {task['id']} requires at least one grader."
            )

    return data


def _json_path(value: Any, path: str) -> Any:
    current = value

    if not path:
        return current

    for part in path.split("."):
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            raise KeyError(path)

    return current


def grade_output(
    output: str,
    grader: dict[str, Any],
) -> float:
    grader_type = grader.get("type")

    if grader_type == "exact":
        expected = str(grader.get("expected", ""))
        return float(output.strip() == expected.strip())

    if grader_type == "regex":
        pattern = grader.get("pattern")

        if not isinstance(pattern, str):
            raise SkillAblateError(
                "regex grader requires a pattern."
            )

        return float(
            re.search(pattern, output, re.MULTILINE) is not None
        )

    if grader_type == "json_equals":
        path = grader.get("path", "")
        expected = grader.get("expected")

        try:
            parsed = json.loads(output)
            actual = _json_path(parsed, path)
        except (json.JSONDecodeError, KeyError, TypeError):
            return 0.0

        return float(actual == expected)

    raise SkillAblateError(
        f"Unsupported grader type: {grader_type}"
    )


def grade_task(
    output: str,
    graders: list[dict[str, Any]],
) -> tuple[float, list[dict[str, Any]]]:
    weighted_total = 0.0
    weight_total = 0.0
    details: list[dict[str, Any]] = []

    for grader in graders:
        weight = float(grader.get("weight", 1.0))

        if weight < 0:
            raise SkillAblateError(
                "Grader weight cannot be negative."
            )

        score = grade_output(output, grader)

        weighted_total += score * weight
        weight_total += weight

        details.append(
            {
                "type": grader.get("type"),
                "weight": weight,
                "score": score,
            }
        )

    if weight_total == 0:
        raise SkillAblateError(
            "Task grader weights cannot sum to zero."
        )

    return weighted_total / weight_total, details


def run_command(
    command: str,
    prompt: str,
    *,
    skill_dir: str | Path | None,
    timeout_seconds: int,
) -> tuple[str, str | None]:
    env = os.environ.copy()

    if skill_dir is None:
        env["SKILLABLATE_SKILL_DIR"] = ""
    else:
        env["SKILLABLATE_SKILL_DIR"] = str(
            Path(skill_dir).resolve()
        )

    try:
        completed = subprocess.run(
            shlex.split(command),
            input=prompt,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            env=env,
            check=False,
        )
    except subprocess.TimeoutExpired:
        return "", f"timeout after {timeout_seconds}s"
    except OSError as exc:
        return "", str(exc)

    if completed.returncode != 0:
        stderr = completed.stderr.strip()

        return (
            completed.stdout.strip(),
            f"exit code {completed.returncode}: {stderr}",
        )

    return completed.stdout.strip(), None


def run_suite(
    suite: dict[str, Any],
    *,
    command: str,
    skill_dir: str | Path,
    trials: int,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    if trials < 1:
        raise SkillAblateError(
            "trials must be at least 1."
        )

    skill_dir = Path(skill_dir)

    if not skill_dir.exists():
        raise SkillAblateError(
            f"Skill directory does not exist: {skill_dir}"
        )

    skill_file = skill_dir / "SKILL.md"

    if not skill_file.exists():
        raise SkillAblateError(
            f"Skill directory has no SKILL.md: {skill_dir}"
        )

    records: list[dict[str, Any]] = []

    for condition in ("baseline", "skill"):
        active_skill = (
            None if condition == "baseline" else skill_dir
        )

        for task in suite["tasks"]:
            for trial_number in range(1, trials + 1):
                output, error = run_command(
                    command,
                    task["prompt"],
                    skill_dir=active_skill,
                    timeout_seconds=timeout_seconds,
                )

                if error:
                    task_score = 0.0
                    grader_results = []
                else:
                    task_score, grader_results = grade_task(
                        output,
                        task["graders"],
                    )

                records.append(
                    {
                        "condition": condition,
                        "task_id": task["id"],
                        "trial": trial_number,
                        "output": output,
                        "error": error,
                        "score": task_score,
                        "graders": grader_results,
                    }
                )

    return {
        "schema_version": "0.1",
        "suite": suite["suite"],
        "command": command,
        "skill_dir": str(skill_dir.resolve()),
        "trials": trials,
        "records": records,
    }


def summarize(result: dict[str, Any]) -> dict[str, float]:
    records = result["records"]

    baseline = [
        float(record["score"])
        for record in records
        if record["condition"] == "baseline"
    ]

    skill = [
        float(record["score"])
        for record in records
        if record["condition"] == "skill"
    ]

    baseline_score = (
        statistics.mean(baseline) if baseline else 0.0
    )

    skill_score = (
        statistics.mean(skill) if skill else 0.0
    )

    return {
        "baseline": baseline_score,
        "skill": skill_score,
        "delta": skill_score - baseline_score,
    }


def format_report(result: dict[str, Any]) -> str:
    summary = summarize(result)
    suite = result["suite"]

    lines = [
        "",
        "SkillAblate",
        "=" * 48,
        f"Suite:    {suite.get('id', 'unknown')}",
        f"Version:  {suite.get('version', 'unknown')}",
        f"Trials:   {result['trials']}",
        "",
        f"Baseline:   {summary['baseline']:.3f}",
        f"With skill: {summary['skill']:.3f}",
        f"Delta:      {summary['delta']:+.3f}",
        "",
        "Per-task results",
        "-" * 48,
    ]

    task_ids = sorted(
        {record["task_id"] for record in result["records"]}
    )

    for task_id in task_ids:
        baseline_scores = [
            record["score"]
            for record in result["records"]
            if record["task_id"] == task_id
            and record["condition"] == "baseline"
        ]

        skill_scores = [
            record["score"]
            for record in result["records"]
            if record["task_id"] == task_id
            and record["condition"] == "skill"
        ]

        b = statistics.mean(baseline_scores)
        s = statistics.mean(skill_scores)

        lines.append(
            f"{task_id}: baseline={b:.3f} "
            f"skill={s:.3f} delta={s - b:+.3f}"
        )

    lines.append("")

    return "\n".join(lines)
