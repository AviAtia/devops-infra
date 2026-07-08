#!/usr/bin/env python3
import argparse
import subprocess
import sys


def run(workspace: str) -> None:
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{workspace}:/src",
        "semgrep/semgrep",
        "semgrep", "scan",
        "--config=auto",
        "--severity=ERROR",
        "--error",
        "/src",
    ]
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("SAST scan failed — critical vulnerabilities found in code.")
        sys.exit(result.returncode)
    print("SAST scan passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Semgrep SAST scan")
    parser.add_argument("--workspace", required=True, help="Path to workspace")
    args = parser.parse_args()
    run(args.workspace)
