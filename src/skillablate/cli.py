from __future__ import annotations

import argparse
import json
from pathlib import Path

from .core import (
    SkillAblateError,
    format_report,
    load_suite,
    run_suite,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="skillablate",
        description=(
            "Measure the effect of an Agent Skill "
            "using paired baseline-vs-skill experiments."
        ),
    )

    subparsers = parser.add_subparsers(
        dest="command_name",
        required=True,
    )

    run_parser = subparsers.add_parser(
        "run",
        help="Run a SkillAblate benchmark.",
    )

    run_parser.add_argument(
        "benchmark",
        help="Path to benchmark YAML.",
    )

    run_parser.add_argument(
        "--skill",
        required=True,
        help="Path to the Agent Skill directory.",
    )

    run_parser.add_argument(
        "--command",
        required=True,
        dest="agent_command",
        help=(
            "Agent command. The prompt is sent via stdin and "
            "SKILLABLATE_SKILL_DIR identifies the treatment skill."
        ),
    )

    run_parser.add_argument(
        "--trials",
        type=int,
        default=3,
        help="Trials per task and condition. Default: 3.",
    )

    run_parser.add_argument(
        "--timeout",
        type=int,
        default=120,
        help="Timeout per trial in seconds. Default: 120.",
    )

    run_parser.add_argument(
        "--output",
        help="Optional path for raw JSON evidence.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    try:
        if args.command_name == "run":
            suite = load_suite(args.benchmark)

            result = run_suite(
                suite,
                command=args.agent_command,
                skill_dir=args.skill,
                trials=args.trials,
                timeout_seconds=args.timeout,
            )

            if args.output:
                output_path = Path(args.output)
                output_path.parent.mkdir(
                    parents=True,
                    exist_ok=True,
                )

                output_path.write_text(
                    json.dumps(
                        result,
                        indent=2,
                        ensure_ascii=False,
                    ),
                    encoding="utf-8",
                )

            print(format_report(result))

    except SkillAblateError as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
