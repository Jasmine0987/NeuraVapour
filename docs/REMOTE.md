# Remote control

The Pi serves a page on port 8000. It can only Start, Stop, Clear fault, and change the setpoint (clamped to `SETPOINT_MIN`..`SETPOINT_MAX`). Safety cutoffs run on the Pi and still work if WiFi drops.

## Stage 1: on your WiFi
`bash deploy/install.sh`, then open `http://<pi-ip>:8000` and paste the token printed by the installer (also in `.env`).

## Stage 2: from anywhere (Tailscale)
```
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```
Install Tailscale on your phone or laptop with the same account, then open `http://<pi-tailscale-name>:8000`. Don't port-forward the Pi through your router.

## Stage 3: online platform (later)
The Pi pushes readings to Supabase/Firebase/MQTT and polls for commands; a web app reads the same data. Same rules: commands limited to start/stop/setpoint, login required, interlocks stay local.

## Limits
Remote control starts and stops the *software*. The Pi must stay powered; for remote power cycling, put a WiFi smart plug on the 12V adapter.
