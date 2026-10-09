from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import click

from tools.release import append_changelog, bump_next_version, check_versions, read_json


ROOT = Path(__file__).resolve().parent.parent


@click.group("logicx-release")
def logicx_release() -> None:
	"""Manage LogicX releases from Bench."""


@logicx_release.command("show")
def show_version() -> None:
	"""Show the current LogicX version."""
	click.echo(f"LogicX version {read_json(ROOT / 'package.json')['version']}")


@logicx_release.command("check")
def check_version() -> None:
	"""Check every LogicX version source."""
	version, failures = check_versions(ROOT)
	if failures:
		details = "\n".join(f"- {failure}" for failure in failures)
		raise click.ClickException(f"Version check failed for {version}:\n{details}")
	click.echo(f"Version check passed for {version}.")


@logicx_release.command("bump")
@click.option("--title", "-t", default="Version update", show_default=True)
@click.option("--database-update/--no-database-update", default=None)
def bump_version(title: str, database_update: bool | None) -> None:
	"""Create the next patch version and changelog section."""
	result = bump_next_version(ROOT, title, database_update)
	click.echo(f"Bumped {result.current_version} -> {result.next_version}")
	click.echo(
		f"Database update: {'yes' if result.database_update.has_update else 'no'} "
		f"({result.database_update.mode})"
	)


@logicx_release.command("append")
@click.option("--title", default="LogicX update", show_default=True)
@click.option("--note", default="Updated LogicX.", show_default=True)
@click.option("--database-update", default="No", show_default=True)
def append_entry(title: str, note: str, database_update: str) -> None:
	"""Append an entry to the current changelog section."""
	append_changelog(ROOT, title, note, database_update)
	version = read_json(ROOT / "package.json")["version"]
	click.echo(f"Added a changelog entry under v-{version}.")


@logicx_release.command(
	"github-now",
	context_settings={"ignore_unknown_options": True, "allow_extra_args": True},
)
@click.pass_context
def github_now(context: click.Context) -> None:
	"""Run the interactive GitHub release workflow."""
	command = [sys.executable, str(ROOT / "tools/github_now.py"), *context.args]
	result = subprocess.run(command, cwd=ROOT, check=False)
	if result.returncode:
		raise click.ClickException(f"GitHub release workflow failed with exit code {result.returncode}.")


commands = [logicx_release]
