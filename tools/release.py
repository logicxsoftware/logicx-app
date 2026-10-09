from __future__ import annotations

import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo


CHANGELOG_PATH = Path("docs/changelog.md")
VERSION_PATTERN = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
CHANGELOG_ENTRY_PATTERN = re.compile(
	r"^### \[v\s+(\d+)\.(\d+)\.(\d+)\]"
	r"(?:\s+\d{4}-\d{2}-\d{2}(?:\s+(?:[1-9]|1[0-2]):[0-5]\d\s+(?:am|pm))?)?"
	r"\s+-\s+(.+)$",
	re.MULTILINE,
)


@dataclass(frozen=True)
class ReleaseEntry:
	version: str
	reference: int
	title: str


@dataclass(frozen=True)
class DatabaseUpdate:
	has_update: bool
	mode: str
	files: tuple[str, ...] = ()


@dataclass(frozen=True)
class BumpResult:
	current_version: str
	next_version: str
	title: str
	database_update: DatabaseUpdate


def read_latest_release(root: Path) -> ReleaseEntry:
	content = (root / CHANGELOG_PATH).read_text(encoding="utf-8")
	match = CHANGELOG_ENTRY_PATTERN.search(content)
	if not match:
		raise ValueError(f"Could not read the latest release from {CHANGELOG_PATH}.")
	title = match.group(4).strip()
	if not title:
		raise ValueError("The latest changelog title is invalid.")
	return ReleaseEntry(
		version=".".join(match.group(index) for index in range(1, 4)),
		reference=int(match.group(3)),
		title=title,
	)


def format_commit_subject(entry: ReleaseEntry) -> str:
	return f"#{entry.reference} - {entry.title}"


def next_patch(version: str) -> str:
	match = VERSION_PATTERN.fullmatch(version)
	if not match:
		raise ValueError(f"Unsupported version format: {version}")
	major, minor, patch = match.groups()
	return f"{major}.{minor}.{int(patch) + 1}"


def bump_next_version(
	root: Path,
	title: str = "Version update",
	database_update: bool | None = None,
) -> BumpResult:
	current_version = read_json(root / "package.json")["version"]
	new_version = next_patch(str(current_version))
	database_state = resolve_database_update(root, database_update)

	update_json_version(root / "package.json", new_version)
	update_json_version(root / "frontend/package.json", new_version)
	update_package_lock(root / "frontend/package-lock.json", new_version)
	replace_required(
		root / "logicx_app/__init__.py",
		re.compile(r'^__version__\s*=\s*["\'][^"\']+["\']', re.MULTILINE),
		f'__version__ = "{new_version}"',
		"Python version",
	)
	replace_required(
		root / "frontend/src/App.jsx",
		re.compile(r"LogicX v\d+\.\d+\.\d+"),
		f"LogicX v{new_version}",
		"sidebar version",
	)
	update_changelog(root, new_version, title, database_state)
	return BumpResult(str(current_version), new_version, title, database_state)


def append_changelog(root: Path, title: str, note: str, database_update: str) -> None:
	version = str(read_json(root / "package.json")["version"])
	section = f"## v-{version}"
	file = root / CHANGELOG_PATH
	content = file.read_text(encoding="utf-8")
	if section not in content:
		raise ValueError(f"Could not find {section}.")
	entry = "\n".join(
		[
			f"### [v {version}] {local_timestamp()} - {title}",
			"",
			"#### Database Changes",
			"",
			f"- Database update: {database_update}.",
			"",
			"#### App Codebase Changes",
			"",
			f"- {note}",
			"",
		]
	)
	file.write_text(content.replace(section, f"{section}\n\n{entry}", 1), encoding="utf-8")


def check_versions(root: Path) -> tuple[str, list[str]]:
	version = str(read_json(root / "package.json")["version"])
	lock = read_json(root / "frontend/package-lock.json")
	expected = [
		("frontend/package.json", str(read_json(root / "frontend/package.json")["version"])),
		("frontend/package-lock.json", str(lock["version"])),
		("frontend/package-lock.json root package", str(lock.get("packages", {}).get("", {}).get("version"))),
		("logicx_app/__init__.py", read_match(root / "logicx_app/__init__.py", r'^__version__\s*=\s*["\']([^"\']+)["\']', "Python version")),
		("App.jsx", read_match(root / "frontend/src/App.jsx", r"LogicX v(\d+\.\d+\.\d+)", "sidebar version")),
	]
	failures = [f"{label} is {actual}; expected {version}." for label, actual in expected if actual != version]
	changelog = (root / CHANGELOG_PATH).read_text(encoding="utf-8")
	for label, value in [
		("current version", f"Current version: {version}"),
		("release tag", f"Release tag: v-{version}"),
		("changelog label", f"Changelog label: v {version}"),
		("version section", f"## v-{version}"),
	]:
		if value not in changelog:
			failures.append(f"The changelog {label} must contain {value}.")
	return version, failures


def resolve_database_update(root: Path, requested: bool | None) -> DatabaseUpdate:
	if requested is not None:
		return DatabaseUpdate(requested, "manual")
	files = tuple(file for file in changed_files(root) if is_database_file(file))
	return DatabaseUpdate(bool(files), "auto-check", files)


def update_changelog(root: Path, version: str, title: str, database_update: DatabaseUpdate) -> None:
	file = root / CHANGELOG_PATH
	content = file.read_text(encoding="utf-8")
	content = re.sub(r"Current version: .*", f"Current version: {version}", content, count=1)
	content = re.sub(r"Release tag: .*", f"Release tag: v-{version}", content, count=1)
	content = re.sub(r"Changelog label: .*", f"Changelog label: v {version}", content, count=1)
	entry = "\n".join(
		[
			f"## v-{version}",
			"",
			f"### [v {version}] {local_timestamp()} - {title}",
			"",
			"#### Database Changes",
			"",
			f"- Database update: {'Yes' if database_update.has_update else 'No'} ({database_update.mode}).",
			"",
			"#### App Codebase Changes",
			"",
			f"- Bumped the LogicX version to {version}.",
			"",
		]
	)
	marker = content.find("## v-")
	insert_at = len(content) if marker == -1 else marker
	file.write_text(f"{content[:insert_at]}{entry}\n{content[insert_at:]}", encoding="utf-8")


def changed_files(root: Path) -> list[str]:
	result = subprocess.run(
		git_command(root, "status", "--porcelain"),
		cwd=root,
		text=True,
		capture_output=True,
		check=False,
	)
	if result.returncode:
		return []
	return [line[3:].split(" -> ")[-1].strip() for line in result.stdout.splitlines() if line]


def git_command(root: Path, *args: str) -> list[str]:
	command = ["git", "-c", f"safe.directory={root}"]
	if os.name == "nt" or root.as_posix().startswith("/workspace/"):
		command.extend(["-c", "core.autocrlf=true", "-c", "core.fileMode=false"])
	return [*command, *args]


def is_database_file(file: str) -> bool:
	normalized = file.replace("\\", "/").lower()
	return "/doctype/" in normalized or "/patches/" in normalized or normalized.endswith("patches.txt")


def read_json(file: Path) -> dict:
	return json.loads(file.read_text(encoding="utf-8"))


def update_json_version(file: Path, version: str) -> None:
	data = read_json(file)
	data["version"] = version
	file.write_text(f"{json.dumps(data, indent=2)}\n", encoding="utf-8")


def update_package_lock(file: Path, version: str) -> None:
	if not file.exists():
		return
	data = read_json(file)
	data["version"] = version
	if "" in data.get("packages", {}):
		data["packages"][""]["version"] = version
	file.write_text(f"{json.dumps(data, indent=2)}\n", encoding="utf-8")


def replace_required(file: Path, pattern: re.Pattern[str], replacement: str, label: str) -> None:
	content = file.read_text(encoding="utf-8")
	updated, count = pattern.subn(replacement, content, count=1)
	if not count:
		raise ValueError(f"Could not update {label} in {file}.")
	file.write_text(updated, encoding="utf-8")


def read_match(file: Path, pattern: str, label: str) -> str:
	match = re.search(pattern, file.read_text(encoding="utf-8"), re.MULTILINE)
	if not match:
		raise ValueError(f"Could not read {label} from {file}.")
	return match.group(1)


def local_timestamp() -> str:
	value = datetime.now(ZoneInfo("Asia/Kolkata"))
	return f"{value:%Y-%m-%d} {value.strftime('%I').lstrip('0')}:{value:%M} {value:%p}".lower()
