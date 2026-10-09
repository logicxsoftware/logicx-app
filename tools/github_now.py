from __future__ import annotations

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from release import (
	bump_next_version,
	check_versions,
	format_commit_subject,
	git_command,
	next_patch,
	read_latest_release,
)


ROOT = Path(__file__).resolve().parent.parent


@dataclass(frozen=True)
class ReleasePlan:
	bump: bool
	title: str


def main() -> int:
	args = parse_args()
	current = read_latest_release(ROOT)
	next_version = next_patch(current.version)
	preview_version = current.version if args.no_bump else next_version
	preview_subject = (
		format_commit_subject(current)
		if args.no_bump
		else f"#{int(preview_version.split('.')[2])} - {args.title}"
	)

	print(f"\n  Current version: {current.version}")
	print(f"  Next version:    {next_version}")
	file_count = show_status()
	if args.dry_run:
		print(render_review(file_count, preview_subject, preview_version))
		print("  Dry run only. No version, pull, commit, or push change was made.\n")
		return 0

	plan = select_release_plan(args, current.title)
	if plan.bump:
		bump_next_version(ROOT, plan.title)
	release = read_latest_release(ROOT)
	default_subject = format_commit_subject(release)
	subject = args.message or default_subject
	if not args.yes:
		subject = ask(f"  Commit message [{default_subject}]: ", default_subject).strip() or default_subject

	validate_versions()
	file_count = len(status_lines())
	confirm_mutation(args, subject, release.version, file_count)
	check_and_pull()
	print("  > git add -A")
	run_git("add", "-A")
	print(f'  > git commit -m "{subject}"')
	run_git("commit", "-m", subject)
	print("  > git push")
	run_git("push")
	print(f"\n  Done - {subject}\n")
	return 0


def select_release_plan(args: argparse.Namespace, current_title: str) -> ReleasePlan:
	if args.yes:
		return ReleasePlan(not args.no_bump, args.title)
	if args.bump:
		answer = "yes"
	elif args.no_bump:
		answer = "no"
	else:
		answer = ask("  Bump next version before commit? [y/N]: ")
	if not is_yes(answer):
		return ReleasePlan(False, current_title)
	title = ask(f"  Version title [{args.title}]: ", args.title).strip() or args.title
	return ReleasePlan(True, title)


def confirm_mutation(args: argparse.Namespace, subject: str, version: str, file_count: int) -> None:
	print(render_review(file_count, subject, version))
	if args.yes:
		return
	if not is_yes(ask("  Continue with pull, stage, commit, and push? [y/N]: ")):
		raise RuntimeError("Cancelled.")


def check_and_pull() -> None:
	upstream = run_git_quiet("rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}")
	if not upstream:
		print("\n  No upstream branch found. Skipping pull.\n")
		return
	print("\n  > git fetch")
	run_git("-c", "maintenance.auto=false", "-c", "gc.auto=0", "fetch", "--quiet")
	behind = int(run_git_quiet("rev-list", "--count", f"HEAD..{upstream}") or "0")
	if not behind:
		print("  Already up to date.\n")
		return
	print(f"  Branch is behind {upstream} by {behind} commit(s).")
	print("  > git pull --rebase --autostash")
	run_git("-c", "maintenance.auto=false", "-c", "gc.auto=0", "pull", "--rebase", "--autostash")


def validate_versions() -> None:
	version, failures = check_versions(ROOT)
	if failures:
		details = "\n".join(f"- {failure}" for failure in failures)
		raise RuntimeError(f"Version check failed for {version}:\n{details}")
	print(f"Version check passed for {version}.")


def show_status() -> int:
	files = status_lines()
	print(f"  Uncommitted: {len(files)} files\n")
	for file in files:
		print(f"    {file}")
	if files:
		print()
	return len(files)


def status_lines() -> list[str]:
	status = run_git("status", "--porcelain", capture=True)
	return [line for line in status.splitlines() if line]


def render_review(file_count: int, subject: str, version: str) -> str:
	rows = ["GitHub Commit Review", f"Version: {version}", f"Subject: {subject}", f"Files: {file_count}"]
	width = max(len(row) for row in rows) + 4
	border = f"+{'-' * width}+"
	body = [f"| {row.ljust(width - 2)} |" for row in rows]
	return "\n".join(["", border, *body, border, ""])


def ask(question: str, default: str = "") -> str:
	if sys.stdin.isatty():
		return input(question) or default
	if os.name == "nt":
		return ask_windows(question, default)
	raise RuntimeError("Interactive input is required. Run this command in a terminal or use --yes.")


def ask_windows(question: str, default: str) -> str:
	if question.rstrip().endswith("[y/N]:"):
		message = question.rsplit("[y/N]:", 1)[0].strip()
		script = (
			"Add-Type -AssemblyName System.Windows.Forms; "
			f"$result = [System.Windows.Forms.MessageBox]::Show({powershell_quote(message)}, "
			"'GitHub Commit Review', 'YesNo', 'Question'); "
			"if ($result -eq 'Yes') { 'yes' } else { 'no' }"
		)
	else:
		script = (
			"Add-Type -AssemblyName Microsoft.VisualBasic; "
			f"[Microsoft.VisualBasic.Interaction]::InputBox({powershell_quote(question)}, "
			f"'GitHub Commit Review', {powershell_quote(default)})"
		)
	return subprocess.check_output(
		["powershell.exe", "-NoProfile", "-STA", "-Command", script],
		cwd=ROOT,
		text=True,
	).strip()


def powershell_quote(value: str) -> str:
	return f"'{value.replace(chr(39), chr(39) * 2)}'"


def is_yes(value: str) -> bool:
	return value.strip().lower() in {"y", "yes"}


def run_git(*args: str, capture: bool = False) -> str:
	result = subprocess.run(
		git_command(ROOT, *args),
		cwd=ROOT,
		text=True,
		capture_output=capture,
		check=True,
	)
	return result.stdout.strip() if capture else ""


def run_git_quiet(*args: str) -> str:
	try:
		return run_git(*args, capture=True)
	except subprocess.CalledProcessError:
		return ""


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Review and publish the current LogicX changes.")
	parser.add_argument("--dry-run", action="store_true")
	parser.add_argument("--no-bump", action="store_true")
	parser.add_argument("--bump", action="store_true")
	parser.add_argument("--yes", action="store_true")
	parser.add_argument("--title", default="Version update")
	parser.add_argument("--message")
	return parser.parse_args()


if __name__ == "__main__":
	try:
		raise SystemExit(main())
	except (OSError, RuntimeError, ValueError, subprocess.CalledProcessError) as error:
		print(f"\n  Error: {error}\n", file=sys.stderr)
		raise SystemExit(1) from None
