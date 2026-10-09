#!/usr/bin/env bash
set -euo pipefail

if [[ "$(id -u)" == "0" ]]; then
	HOST_GID="${HOST_GID:-1000}"
	mkdir -p /home/devops/persistent /home/devops/.cache/uv \
		/workspace/logicx-app/node_modules /workspace/logicx-app/frontend/node_modules
	chown -R devops:devops /home/devops/persistent /home/devops/.cache \
		/workspace/logicx-app/node_modules /workspace/logicx-app/frontend/node_modules
	# Keep the host-mounted Bench writable from code-server. The setgid bit makes
	# files created by the container inherit the host developer's group.
	chgrp -R "$HOST_GID" /home/devops/persistent
	chmod -R g+rwX /home/devops/persistent
	find /home/devops/persistent -type d -exec chmod g+s {} +
	export HOME=/home/devops XDG_CACHE_HOME=/home/devops/.cache
	exec runuser -u devops --preserve-environment -- "$0" "$@"
fi

init-frappe
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
