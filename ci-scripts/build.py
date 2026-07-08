#!/usr/bin/env python3
import argparse
import subprocess
import sys


def run(image_name: str, image_tag: str, extra_tags: list) -> None:
    cmd = ["docker", "build"]
    cmd += ["-t", f"{image_name}:{image_tag}"]
    for tag in extra_tags:
        cmd += ["-t", f"{image_name}:{tag}"]
    cmd.append(".")

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("Docker build failed.")
        sys.exit(result.returncode)
    print(f"Image built: {image_name}:{image_tag}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build Docker image")
    parser.add_argument("--image-name", required=True, help="Image name (e.g. user/app)")
    parser.add_argument("--image-tag", required=True, help="Primary image tag")
    parser.add_argument("--extra-tags", nargs="*", default=[], help="Additional tags (e.g. latest)")
    args = parser.parse_args()
    run(args.image_name, args.image_tag, args.extra_tags)
