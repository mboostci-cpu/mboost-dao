#!/usr/bin/env bash
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo 'Exécuter sur le VPS en root.'; exit 1; }
cd "$(dirname "$0")/.."
[ "$PWD" = /opt/mboost-cv-dao ] || { echo 'Installer dans /opt/mboost-cv-dao.'; exit 1; }
apt-get update -qq
apt-get install -y python3-venv antiword poppler-utils tesseract-ocr tesseract-ocr-fra tesseract-ocr-eng
id mboostcv >/dev/null 2>&1 || useradd --system --home /var/lib/mboost-cv-dao --shell /usr/sbin/nologin mboostcv
install -d -m 700 -o mboostcv -g mboostcv /var/lib/mboost-cv-dao
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
if [ ! -f /etc/mboost-cv-dao.env ]; then
 install -m 600 /dev/null /etc/mboost-cv-dao.env
 cat > /etc/mboost-cv-dao.env <<'ENV'
DATA_DIR=/var/lib/mboost-cv-dao
MODEL_PROVIDER=
OPENAI_API_KEY=
OPENAI_MODEL=
ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=
MAX_UPLOAD_MB=12
MAX_PAGES=250
PUBLIC_MODE=0
ENV
fi
install -m 644 deploy/mboost-cv-web.service deploy/mboost-cv-worker.service /etc/systemd/system/
install -m 644 deploy/mboost-cv-backup.service deploy/mboost-cv-backup.timer /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now mboost-cv-web mboost-cv-worker mboost-cv-backup.timer
curl --fail --silent http://127.0.0.1:8012/health
