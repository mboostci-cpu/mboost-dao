#!/usr/bin/env bash
set -euo pipefail
backup_dir=/var/backups/mboost-cv-dao
install -d -m 700 "$backup_dir"
trap 'systemctl start mboost-cv-web mboost-cv-worker' EXIT
systemctl stop mboost-cv-web mboost-cv-worker
tar -czf "$backup_dir/$(date -u +%Y%m%dT%H%M%SZ).tgz" /var/lib/mboost-cv-dao /etc/mboost-cv-dao.env
chmod 600 "$backup_dir"/*.tgz
