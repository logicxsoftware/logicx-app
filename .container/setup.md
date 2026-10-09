# LogicX local deployment

This Compose stack creates a persistent Frappe v16 site, installs ERPNext, links the local `logicx_app`
source, installs the app, and runs migrations automatically.

## 1. Open the repository

```powershell
cd E:\codexsun\logicx-app
```

Run all remaining commands from this directory.

## 2. Optional configuration

Create a root `.env` only when changing defaults:

```dotenv
SITE_NAME=logicx.localhost
HTTP_PORT=8000
SOCKETIO_PORT=9000
ADMIN_PASSWORD=admin
DB_ROOT_PASSWORD=logicx_db_root
FRAPPE_BRANCH=version-16
ERPNEXT_BRANCH=version-16
FRAPPE_BENCH_HOST_PATH=/home/logicx/frappe-bench
HOST_GID=1000
```

Keep real passwords out of Git.

## 3. Build the LogicX interface

```powershell
npm.cmd install
npm.cmd run build
```

This compiles the React application served at `/logicx-app`.

## 4. Build and start

```powershell
docker compose -f .container/compose.yml up -d --build
```

The first build downloads and compiles the Frappe runtime, so it takes longer than later starts.

## 5. Follow installation

```powershell
docker compose -f .container/compose.yml logs -f frappe
```

Wait for `LogicX is ready`. Press `Ctrl+C` to stop following logs; containers keep running.

## 6. Open the site

Open <http://localhost:8000/logicx-app> and sign in as `Administrator` with the configured admin password.

Use the LogicX app for product management, or open `/app/logicx-app` for its native Desk workspace.

## 7. Verify installation

```powershell
docker compose -f .container/compose.yml exec -w /home/devops/persistent/frappe-bench frappe bench --site logicx.localhost list-apps
docker compose -f .container/compose.yml exec -w /home/devops/persistent/frappe-bench frappe bench --site logicx.localhost migrate
```

The app list must contain `frappe`, `erpnext`, and `logicx_app`.

## 8. Apply source changes

Run migrations, rebuild the app assets inside the Linux container, and clear cached Desk data:

```powershell
docker compose -f .container/compose.yml exec -w /home/devops/persistent/frappe-bench frappe bench --site logicx.localhost migrate
docker compose -f .container/compose.yml exec -w /workspace/logicx-app frappe npm --prefix frontend install
docker compose -f .container/compose.yml exec -w /home/devops/persistent/frappe-bench frappe bench build --app logicx_app
docker compose -f .container/compose.yml exec -w /home/devops/persistent/frappe-bench frappe bench --site logicx.localhost clear-cache
```

Docker keeps Linux dependencies in separate named volumes, so they do not conflict with Windows `node_modules`.

## 9. Product integration

- **Add product** creates an ERPNext Item and its linked LogicX Product in one transaction.
- **Link existing item** creates only the LogicX Product. It does not change the ERPNext Item.
- LogicX Product stores the catalog text, status, organization, media, variants, prices, stock, and highlights.

If `logicx-test.localhost` exists, run the isolated product tests after an integration change:

```powershell
docker compose -f .container/compose.yml exec -T -w /home/devops/persistent/frappe-bench frappe bench --site logicx-test.localhost run-tests --module logicx_app.logicx.doctype.logicx_product.test_logicx_product
```

## 10. Stop or start later

```powershell
docker compose -f .container/compose.yml stop
docker compose -f .container/compose.yml start
```

The host directory `/home/logicx/frappe-bench` preserves the Bench and can be
opened directly in code-server. MariaDB remains in its named Docker volume.

## 11. Remove the local deployment

```powershell
docker compose -f .container/compose.yml down
```

This keeps data. To also delete the local database volume, explicitly run:

```powershell
docker compose -f .container/compose.yml down --volumes
```

The `--volumes` command permanently removes the MariaDB deployment data. It
does not remove the host Bench directory.
