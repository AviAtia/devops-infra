#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys


def bump_patch(version: str) -> str:
    major, minor, patch = version.split(".")
    return f"{major}.{minor}.{int(patch) + 1}"


def update_json_version(filepath: str, new_version: str, root_only: bool = False) -> None:
    with open(filepath, "r") as f:
        data = json.load(f)
    data["version"] = new_version
    if root_only is False and "packages" in data and "" in data["packages"]:
        data["packages"][""]["version"] = new_version
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def run(git_user: str, git_token: str, repo: str, git_email: str, git_name: str) -> None:
    with open("package.json", "r") as f:
        data = json.load(f)
    current = data["version"]
    new_version = bump_patch(current)
    print(f"Bumping version: {current} → {new_version}")

    update_json_version("package.json", new_version, root_only=True)
    update_json_version("package-lock.json", new_version)

    cmds = [
        ["git", "config", "user.email", git_email],
        ["git", "config", "user.name", git_name],
        ["git", "add", "package.json", "package-lock.json"],
        ["git", "commit", "-m", f"[version bump] v{new_version}"],
        ["git", "tag", "-a", f"v{new_version}", "-m", f"v{new_version}"],
        ["git", "push", f"https://{git_user}:{git_token}@github.com/{repo}.git",
         "HEAD:main", "--follow-tags"],
    ]

    for cmd in cmds:
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"Command failed: {' '.join(cmd)}")
            sys.exit(result.returncode)

    print(f"Version bumped to {new_version} and pushed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bump patch version and push to GitHub")
    parser.add_argument("--git-user", required=True)
    parser.add_argument("--git-token", required=True)
    parser.add_argument("--repo", required=True, help="GitHub repo (e.g. AviAtia/sample-nodejs-devops)")
    parser.add_argument("--git-email", default="ci@devopschallenge.com")
    parser.add_argument("--git-name", default="Jenkins")
    args = parser.parse_args()
    run(args.git_user, args.git_token, args.repo, args.git_email, args.git_name)
