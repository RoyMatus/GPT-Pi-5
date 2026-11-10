#!/bin/sh
# Install a previously built wheel as the current desktop user, without sudo.
set -eu
wheel=$(realpath "${1:?Pass the built gpt_pi_5 wheel}")
test -f "$wheel"
case "$wheel" in */gpt_pi_5-*.whl) ;; *) echo 'Expected a GPT-Pi wheel' >&2; exit 1;; esac
root="$HOME/.local/opt/gpt-pi"
release="$root/releases/$(date +%Y%m%d-%H%M%S)"
mkdir -p "$release" "$HOME/.config/systemd/user" "$HOME/.config/autostart" "$HOME/.local/bin"
chmod 700 "$root" "$release"
python3 -m venv "$release/venv"
"$release/venv/bin/python" -m pip install "$wheel"
"$release/venv/bin/python" -c 'from gpt_pi.webapp import create_app; from importlib.resources import files; assert files("gpt_pi").joinpath("web/assets/app.js").is_file()'
previous=''
if test -e "$root/current"; then
    previous=$(readlink -f "$root/current")
    case "$previous" in "$root"/releases/*) ;; *) echo 'Unexpected current installation; stop.' >&2; exit 1;; esac
    printf '%s\n' "$previous" > "$root/previous-release"
fi
if test -f "$HOME/.config/systemd/user/gpt-pi.service"; then
    cp "$HOME/.config/systemd/user/gpt-pi.service" "$release/service-before-install"
fi
cat > "$HOME/.config/systemd/user/gpt-pi.service" <<EOF
[Unit]
Description=GPT-Pi 5 personal assistant
After=network.target

[Service]
Type=simple
WorkingDirectory=$root/current
ExecStart=$root/current/venv/bin/python -m gpt_pi
Environment=GPT_PI_PROVIDER=chatgpt
Environment=GPT_PI_PORT=8765
Environment=GPT_PI_DATA_DIR=$HOME/.local/share/gpt-pi
Environment=PYTHONDONTWRITEBYTECODE=1
Restart=on-failure
RestartSec=3
NoNewPrivileges=true
PrivateTmp=true
UMask=0077

[Install]
WantedBy=default.target
EOF
ln -s "$release" "$root/current.next"
mv -Tf "$root/current.next" "$root/current"
systemctl --user daemon-reload
systemctl --user enable gpt-pi.service
systemctl --user restart gpt-pi.service
ready=0
for attempt in 1 2 3 4 5 6 7 8 9 10; do
    if curl --fail --silent http://127.0.0.1:8765/health >/dev/null; then ready=1; break; fi
    sleep 1
done
if test "$ready" != 1; then
    systemctl --user stop gpt-pi.service
    if test -n "$previous"; then
        ln -s "$previous" "$root/rollback.next"
        mv -Tf "$root/rollback.next" "$root/current"
        if test -f "$release/service-before-install"; then
            cp "$release/service-before-install" "$HOME/.config/systemd/user/gpt-pi.service"
        fi
        systemctl --user daemon-reload
        systemctl --user start gpt-pi.service
    fi
    echo 'Installation failed health check; previous release restored if present.' >&2
    exit 1
fi
cat > "$HOME/.local/bin/gpt-pi-kiosk" <<'EOF'
#!/bin/sh
set -eu
export XDG_RUNTIME_DIR="${XDG_RUNTIME_DIR:-/run/user/$(id -u)}"
for attempt in $(seq 1 40); do
    if curl --fail --silent http://127.0.0.1:8765/health >/dev/null; then break; fi
    sleep .5
done
# The desktop owns squeekboard startup. A second instance can claim the input
# method before losing the D-Bus name, leaving the surviving instance unusable.
# Fullscreen windows cover squeekboard's top layer on labwc; use a maximized app.
exec chromium --start-maximized --app=http://127.0.0.1:8765 --incognito --no-first-run --no-default-browser-check --ozone-platform=wayland --enable-wayland-ime --wayland-text-input-version=3 --user-data-dir="$HOME/.local/share/gpt-pi-browser"
EOF
chmod 700 "$HOME/.local/bin/gpt-pi-kiosk"
cat > "$HOME/.config/autostart/gpt-pi.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=GPT-Pi 5
Comment=Personal assistant with ChatGPT sign-in
Exec=$HOME/.local/bin/gpt-pi-kiosk
Terminal=false
EOF
printf 'Installed and started: %s\n' "$release"
