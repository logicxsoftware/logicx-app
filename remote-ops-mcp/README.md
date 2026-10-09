# LogicX Remote Operations MCP

This is the LogicX-local copy of the controlled stdio MCP setup. It provides token authentication, exact SSH command allowlisting, JSONL audit logging, LogicX repository verification, and MCP tools for runtime and cloud operations.

Set `CODEXSUN_MCP_API_TOKEN` in the environment inherited by the MCP client. Use at least 16 characters. Set `CODEXSUN_MCP_REQUIRE_REQUEST_TOKEN=1` when a bridge supplies a bearer token in MCP request metadata.

Add the supplied [`logicx-mcp.example.json`](./logicx-mcp.example.json) fragment to the MCP client configuration. Do not place the API token, SSH private key, or server password in that JSON file.

Configure the LogicX remote with environment JSON:

```text
CODEXSUN_MCP_SSH_TARGETS={"logicx":{"host":"YOUR_LOGICX_HOST","user":"YOUR_LOGIN_USER","port":22,"keyPath":"E:/path/to/logicx_ed25519"}}
CODEXSUN_MCP_SSH_ALLOWED_COMMANDS={"logicx":["docker compose ps","docker compose logs --tail=100 frappe"]}
```

The server uses OpenSSH key authentication with `BatchMode=yes` and `StrictHostKeyChecking=yes`. It never accepts a request-provided key, host, or arbitrary command. Every operation is appended to `storage/runtime/remote-mcp-audit.jsonl` unless `CODEXSUN_MCP_AUDIT_PATH` overrides the path.

Available tools are `registry.list`, `registry.verify`, `runtime.status`, `cloud.ssh.status`, and `cloud.ssh.exec`. The registry is LogicX-specific and validates the Frappe app, React frontend, and container setup files.

Run checks from the repository root:

```powershell
npm.cmd run mcp:check
npm.cmd run mcp:test
```
