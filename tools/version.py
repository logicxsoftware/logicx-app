from __future__ import annotations

import argparse
from pathlib import Path

from release import append_changelog, bump_next_version, check_versions, read_json


ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
	args = parse_args()
	if args.command == "show":
		print(f"LogicX version {read_json(ROOT / 'package.json')['version']}")
		return 0
	if args.command == "check":
		return run_check()
	if args.command == "append":
		append_changelog(ROOT, args.title, args.note, args.database_update)
		print(f"Added a changelog entry under v-{read_json(ROOT / 'package.json')['version']}.")
		return 0

	database_update = True if args.database_update else False if args.no_database_update else None
	result = bump_next_version(ROOT, args.title, database_update)
	print(f"Bumped {result.current_version} -> {result.next_version}")
	print(
		f"Database update: {'yes' if result.database_update.has_update else 'no'} "
		f"({result.database_update.mode})"
	)
	return 0


def run_check() -> int:
	version, failures = check_versions(ROOT)
	if failures:
		print(f"Version check failed for {version}:")
		for failure in failures:
			print(f"- {failure}")
		return 1
	print(f"Version check passed for {version}.")
	return 0


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Manage the LogicX version and changelog.")
	subparsers = parser.add_subparsers(dest="command", required=True)
	subparsers.add_parser("show")
	subparsers.add_parser("check")

	bump = subparsers.add_parser("bump")
	bump.add_argument("--title", "-t", default="Version update")
	database_group = bump.add_mutually_exclusive_group()
	database_group.add_argument("--database-update", action="store_true")
	database_group.add_argument("--no-database-update", action="store_true")

	append = subparsers.add_parser("append")
	append.add_argument("--title", default="LogicX update")
	append.add_argument("--note", default="Updated LogicX.")
	append.add_argument("--database-update", default="No")
	return parser.parse_args()


if __name__ == "__main__":
	raise SystemExit(main())
