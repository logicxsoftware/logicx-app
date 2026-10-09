import { access, readFile } from "node:fs/promises";
import { join } from "node:path";

const requiredFiles = [
  "package.json",
  "pyproject.toml",
  "logicx_app/hooks.py",
  "frontend/package.json",
  ".container/compose.yml",
];

export function loadRegistry(repositoryRoot) {
  return {
    applications: [
      { id: "logicx", label: "LogicX", owner: "logicx_app", category: "frappe" },
    ],
    repositoryRoot,
  };
}

export async function verifyRegistry(repositoryRoot) {
  const checks = await Promise.all(requiredFiles.map(async (file) => ({
    file,
    present: await exists(join(repositoryRoot, file)),
  })));
  const packageJson = await readJson(join(repositoryRoot, "package.json"));
  const appName = packageJson?.name || null;
  return {
    ok: checks.every((check) => check.present) && appName === "logicx-app",
    application: "logicx",
    appName,
    checks,
  };
}

async function exists(file) {
  try {
    await access(file);
    return true;
  } catch {
    return false;
  }
}

async function readJson(file) {
  try {
    return JSON.parse(await readFile(file, "utf8"));
  } catch {
    return null;
  }
}
