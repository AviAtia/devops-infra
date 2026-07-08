#!/usr/bin/env python3
import argparse
import subprocess
import sys


def run(image_name: str, image_tag: str, username: str, password: str) -> None:
    login = subprocess.run(
        ["docker", "login", "-u", username, "--password-stdin"],
        input=password.encode(),
    )
    if login.returncode != 0:
        print("Docker login failed.")
        sys.exit(login.returncode)

    for tag in [image_tag, "latest"]:
        result = subprocess.run(["docker", "push", f"{image_name}:{tag}"])
        if result.returncode != 0:
            print(f"Failed to push {image_name}:{tag}")
            sys.exit(result.returncode)
        print(f"Pushed {image_name}:{tag}")

    subprocess.run(["docker", "logout"])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push Docker image to registry")
    parser.add_argument("--image-name", required=True)
    parser.add_argument("--image-tag", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    run(args.image_name, args.image_tag, args.username, args.password)
