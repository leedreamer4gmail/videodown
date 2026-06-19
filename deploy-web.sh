#!/usr/bin/env bash
# 部署 Web 版到远程服务器
set -euo pipefail

REMOTE="admin@8.219.6.216"
TARGET="/home/project/videodown"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "→ 同步文件到 $REMOTE:$TARGET"
rsync -avz --delete \
  --exclude '.venv' \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  --exclude '.git' \
  --exclude 'downloads' \
  --exclude 'VideoDown.desktop' \
  "$ROOT/videodown" \
  "$ROOT/requirements-web.txt" \
  "$ROOT/run-web.sh" \
  "$ROOT/deploy/" \
  "$REMOTE:$TARGET/"

echo "→ 远程安装依赖并启动服务"
ssh "$REMOTE" bash -s <<'REMOTE_SCRIPT'
set -euo pipefail
cd /home/project/videodown
python3 -m venv .venv
.venv/bin/pip install --quiet -r requirements-web.txt
chmod +x run-web.sh
mkdir -p downloads
sudo cp deploy/videodown-web.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable videodown-web
sudo systemctl restart videodown-web
sleep 1
sudo systemctl is-active videodown-web
curl -sf http://127.0.0.1:8765/ | head -3
REMOTE_SCRIPT

echo "✓ 部署完成"
echo "  内网: http://127.0.0.1:8765"
echo "  若已配置 Nginx: https://leedreamer.cn/videodown/"
