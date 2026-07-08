#!/usr/bin/env python3
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile


def update_values_yaml(values_file: str, new_tag: str) -> None:
    with open(values_file, 'r') as f:
        content = f.read()
    updated = re.sub(r'(^\s*tag:\s*).*$', rf'\1"{new_tag}"', content, flags=re.MULTILINE)
    with open(values_file, 'w') as f:
        f.write(updated)
    print(f"Updated image tag to {new_tag}")


def run(git_user: str, git_token: str, repo: str, image_tag: str,
        values_path: str, git_email: str, git_name: str) -> None:

    tmp_dir = tempfile.mkdtemp()
    try:
        clone_url = f"https://{git_user}:{git_token}@github.com/{repo}.git"
        result = subprocess.run(["git", "clone", clone_url, tmp_dir])
        if result.returncode != 0:
            print("Failed to clone GitOps repo.")
            sys.exit(1)

        values_file = os.path.join(tmp_dir, values_path)
        update_values_yaml(values_file, image_tag)

        cmds = [
            ["git", "-C", tmp_dir, "config", "user.email", git_email],
            ["git", "-C", tmp_dir, "config", "user.name", git_name],
            ["git", "-C", tmp_dir, "add", values_file],
            ["git", "-C", tmp_dir, "commit", "-m", f"[ci] update image tag to {image_tag}"],
            ["git", "-C", tmp_dir, "push", clone_url, "HEAD:main"],
        ]

        for cmd in cmds:
            result = subprocess.run(cmd)
            if result.returncode != 0:
                print(f"Command failed: {' '.join(cmd)}")
                sys.exit(result.returncode)

        print(f"Helm values updated and pushed — ArgoCD will deploy {image_tag}")
    finally:
        shutil.rmtree(tmp_dir)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update Helm chart image tag in a GitOps repo")
    parser.add_argument("--git-user", required=True)
    parser.add_argument("--git-token", required=True)
    parser.add_argument("--repo", required=True, help="GitOps repo (e.g. AviAtia/devops-infra)")
    parser.add_argument("--image-tag", required=True, help="New image tag to deploy")
    parser.add_argument("--values-path", default="helm/sample-nodejs/values.yaml",
                        help="Path to values.yaml inside the GitOps repo")
    parser.add_argument("--git-email", default="ci@devopschallenge.com")
    parser.add_argument("--git-name", default="Jenkins")
    args = parser.parse_args()
    run(args.git_user, args.git_token, args.repo, args.image_tag,
        args.values_path, args.git_email, args.git_name)
