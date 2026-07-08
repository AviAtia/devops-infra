#!/usr/bin/env python3
import argparse
import subprocess
import sys


def run(image: str, ignore_unfixed: bool, skip_dirs: list) -> None:
    cmd = [
        "trivy", "image",
        "--exit-code", "1",
        "--severity", "HIGH,CRITICAL",
        "--no-progress",
    ]
    for d in skip_dirs:
        cmd += ["--skip-dirs", d]
    if ignore_unfixed:
        cmd.append("--ignore-unfixed")
    cmd.append(image)

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Trivy scan failed — HIGH/CRITICAL vulnerabilities found.")
        sys.exit(result.returncode)
    print("Trivy scan passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Trivy image vulnerability scan")
    parser.add_argument("--image", required=True, help="Docker image to scan (name:tag)")
    parser.add_argument("--ignore-unfixed", action="store_true", default=True,
                        help="Ignore vulnerabilities with no fix available")
    parser.add_argument("--no-ignore-unfixed", dest="ignore_unfixed", action="store_false",
                        help="Show all vulnerabilities including unfixed")
    parser.add_argument("--skip-dirs", nargs="*", default=[
        "/usr/local/lib/node_modules/npm",
        "/usr/local/lib/node_modules/corepack",
        "/opt/yarn-v1.22.22",
    ], help="Directories to skip during scan")
    args = parser.parse_args()
    run(args.image, args.ignore_unfixed, args.skip_dirs)
