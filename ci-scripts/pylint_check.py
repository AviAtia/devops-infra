#!/usr/bin/env python3
import argparse
import subprocess
import sys


def run(path: str, min_score: float, fail_on_warnings: bool) -> None:
    disable = "C,R" if fail_on_warnings else "C,R,W"
    cmd = [
        "pylint", path,
        f"--disable={disable}",
        f"--fail-under={min_score}",
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"Pylint check failed — score below {min_score} or errors found.")
        sys.exit(result.returncode)
    print("Pylint check passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run pylint on Python source files")
    parser.add_argument("--path", required=True, help="File or directory to lint")
    parser.add_argument("--min-score", type=float, default=7.0,
                        help="Minimum pylint score (default: 7.0)")
    parser.add_argument("--fail-on-warnings", action="store_true", default=False,
                        help="Also fail on warnings (default: errors only)")
    args = parser.parse_args()
    run(args.path, args.min_score, args.fail_on_warnings)
