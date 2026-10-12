#!/usr/bin/env bash
# Run on the Pi from anywhere:  bash deploy/install.sh
set -e
cd "$(dirname "$0")/.."
sudo apt install -y python3-flask
if [ ! -f .env ]; then
  TOKEN=$(python3 -c "import secrets;print(secrets.token_urlsafe(24))")
  printf "MD_TOKEN=%s\nMD_AUTO_START=0\n" "$TOKEN" > .env
  chmod 600 .env
  echo "Created .env. Your access token for the web page is: $TOKEN"
fi
sed "s|__USER__|$USER|g; s|__DIR__|$PWD|g" deploy/mdchamber.service | sudo tee /etc/systemd/system/mdchamber.service >/dev/null
sudo systemctl daemon-reload
sudo systemctl enable --now mdchamber
echo "Service installed. Page: http://$(hostname -I | awk '{print $1}'):8000"
echo "Logs: journalctl -u mdchamber -f"
