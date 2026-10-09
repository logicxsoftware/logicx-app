#!/usr/bin/env python3
"""Create or upgrade the persistent LogicX Frappe bench."""

from __future__ import annotations

import os
import pathlib
import subprocess
import time


# The host bind mount defaults to /home/logicx/frappe-bench.  Within the
# container, Compose exposes its parent directory at this stable path.
PERSISTENT_DIR = pathlib.Path(os.getenv("FRAPPE_PERSISTENT_DIR", "/home/devops/persistent"))
BENCH_DIR = PERSISTENT_DIR / "frappe-bench"
APP_SOURCE = pathlib.Path("/workspace/logicx-app")
SITE_NAME = os.getenv("SITE_NAME", "logicx.localhost")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin")
DB_HOST = os.getenv("DB_HOST", "mariadb")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_ROOT_PASSWORD = os.getenv("DB_ROOT_PASSWORD", "logicx_db_root")
FRAPPE_BRANCH = os.getenv("FRAPPE_BRANCH", "version-16")
ERPNEXT_BRANCH = os.getenv("ERPNEXT_BRANCH", "version-16")


def run(*command: str, cwd: pathlib.Path | None = None) -> None:
	print(f"+ {' '.join(command)}", flush=True)
	subprocess.run(command, cwd=cwd, check=True)


def output(*command: str, cwd: pathlib.Path | None = None) -> str:
	return subprocess.check_output(command, cwd=cwd, text=True).strip()


def wait_for_database() -> None:
	for _ in range(60):
		result = subprocess.run(
			[
				"mariadb-admin",
				"ping",
				f"--host={DB_HOST}",
				f"--port={DB_PORT}",
				"--user=root",
				f"--password={DB_ROOT_PASSWORD}",
				"--silent",
			],
			check=False,
		)
		if result.returncode == 0:
			return
		time.sleep(2)
	raise RuntimeError("MariaDB did not become ready")


def ensure_bench() -> None:
	if (BENCH_DIR / "apps/frappe").is_dir():
		return
	BENCH_DIR.mkdir(parents=True, exist_ok=True)
	if any(BENCH_DIR.iterdir()):
		raise RuntimeError(f"{BENCH_DIR} is not empty but is not a Frappe bench")
	BENCH_DIR.rmdir()
	run(
		"bench",
		"init",
		str(BENCH_DIR),
		"--frappe-branch",
		FRAPPE_BRANCH,
	)


def ensure_bench_timezone_data() -> None:
	bench_python = BENCH_DIR / "env/bin/python"
	check = subprocess.run(
		[str(bench_python), "-c", "import tzdata"],
		check=False,
		stdout=subprocess.DEVNULL,
		stderr=subprocess.DEVNULL,
	)
	if check.returncode == 0:
		return
	run(str(bench_python), "-m", "pip", "install", "--no-deps", "tzdata")


def ensure_erpnext() -> None:
	if (BENCH_DIR / "apps/erpnext").is_dir():
		return
	run(
		"bench",
		"get-app",
		"erpnext",
		"https://github.com/frappe/erpnext.git",
		"--branch",
		ERPNEXT_BRANCH,
		cwd=BENCH_DIR,
	)


def link_logicx() -> None:
	if not (APP_SOURCE / "pyproject.toml").is_file():
		raise RuntimeError(f"LogicX source is missing at {APP_SOURCE}")
	target = BENCH_DIR / "apps/logicx_app"
	if target.is_symlink():
		target.unlink()
	elif target.exists():
		raise RuntimeError(f"Refusing to replace non-symlinked app directory: {target}")
	target.symlink_to(APP_SOURCE, target_is_directory=True)
	run(str(BENCH_DIR / "env/bin/python"), "-m", "pip", "install", "--no-deps", "-e", str(APP_SOURCE))
	apps_file = BENCH_DIR / "sites/apps.txt"
	apps = [line.strip() for line in apps_file.read_text(encoding="utf-8").splitlines() if line.strip()]
	if "logicx_app" not in apps:
		apps_file.write_text("\n".join([*apps, "logicx_app"]) + "\n", encoding="utf-8")


def ensure_site() -> None:
	site_path = BENCH_DIR / "sites" / SITE_NAME
	if not site_path.is_dir():
		run(
			"bench",
			"new-site",
			SITE_NAME,
			"--admin-password",
			ADMIN_PASSWORD,
			"--db-host",
			DB_HOST,
			"--db-port",
			DB_PORT,
			"--mariadb-root-username",
			"root",
			"--mariadb-root-password",
			DB_ROOT_PASSWORD,
			"--mariadb-user-host-login-scope=%",
			cwd=BENCH_DIR,
		)
	run("bench", "use", SITE_NAME, cwd=BENCH_DIR)
	run("bench", "set-config", "-g", "serve_default_site", "true", cwd=BENCH_DIR)


def installed_apps() -> set[str]:
	value = output("bench", "--site", SITE_NAME, "list-apps", "--format", "json", cwd=BENCH_DIR)
	import json

	return set(json.loads(value))


def start_bootstrap_redis() -> None:
	for config_name in ("redis_queue.conf", "redis_cache.conf"):
		run(
			"redis-server",
			str(BENCH_DIR / "config" / config_name),
			"--daemonize",
			"yes",
		)


def stop_bootstrap_redis() -> None:
	for port in (11000, 13000):
		subprocess.run(["redis-cli", "-p", str(port), "shutdown"], check=False)


def install_and_migrate() -> None:
	start_bootstrap_redis()
	try:
		apps = installed_apps()
		if "erpnext" not in apps:
			run("bench", "--site", SITE_NAME, "install-app", "erpnext", cwd=BENCH_DIR)
		if "logicx_app" not in apps:
			run("bench", "--site", SITE_NAME, "install-app", "logicx_app", cwd=BENCH_DIR)
		run("bench", "--site", SITE_NAME, "migrate", cwd=BENCH_DIR)
	finally:
		stop_bootstrap_redis()


def main() -> None:
	wait_for_database()
	ensure_bench()
	ensure_bench_timezone_data()
	ensure_erpnext()
	link_logicx()
	ensure_site()
	install_and_migrate()
	print(f"LogicX is ready at http://localhost:8000 (site: {SITE_NAME})", flush=True)


if __name__ == "__main__":
	main()
