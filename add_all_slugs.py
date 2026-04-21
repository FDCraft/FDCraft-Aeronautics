#!/usr/bin/env python3
"""Read slugs from pakku-lock.json and run pakku add commands in batch."""

import json
import subprocess
import sys
from pathlib import Path


def collect_slugs(lock_data):
    """Collect all slug values from projects while preserving order and removing duplicates."""
    seen = set()
    ordered = []

    for project in lock_data.get("projects", []):
        slug_obj = project.get("slug")
        if not isinstance(slug_obj, dict):
            continue

        for slug in slug_obj.values():
            if isinstance(slug, str) and slug and slug not in seen:
                seen.add(slug)
                ordered.append(slug)

    return ordered


def run_add_commands(slugs, pakku_jar):
    failures = []

    for index, slug in enumerate(slugs, start=1):
        cmd = ["java", "-jar", str(pakku_jar), "--yes", "add", slug]
        print(f"[{index}/{len(slugs)}] Running: {' '.join(cmd)}")

        result = subprocess.run(cmd, check=False)
        if result.returncode != 0:
            failures.append((slug, result.returncode))

    return failures


def main():
    root = Path(__file__).resolve().parent
    lock_file = root / "pakku-lock.json"
    pakku_jar = root / "pakku.jar"

    if not lock_file.exists():
        print(f"Error: {lock_file} not found", file=sys.stderr)
        return 1

    if not pakku_jar.exists():
        print(f"Error: {pakku_jar} not found", file=sys.stderr)
        return 1

    with lock_file.open("r", encoding="utf-8") as f:
        lock_data = json.load(f)

    slugs = collect_slugs(lock_data)
    if not slugs:
        print("No slugs found in pakku-lock.json")
        return 0

    print(f"Found {len(slugs)} unique slugs. Start adding...")
    failures = run_add_commands(slugs, pakku_jar)

    if failures:
        print("\nFinished with failures:")
        for slug, code in failures:
            print(f"- {slug}: exit code {code}")
        return 2

    print("\nAll slug add commands completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
