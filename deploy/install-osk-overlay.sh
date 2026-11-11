#!/bin/sh
# Explicit Pi setup, as the desktop user. Requires cc/pkg-config/libglib2.0-dev.
set -eu
source_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
root="$HOME/.local/lib/gpt-pi-osk"
desktop_source=/etc/xdg/autostart/squeekboard.desktop
test -f "$desktop_source"
pkg-config --exists gobject-2.0
mkdir -p "$root" "$HOME/.local/bin" "$HOME/.config/autostart"
chmod 700 "$root"
# GTK3 soname avoids requiring the entire GTK development stack on the display.
# pkg-config supplies tokenized compiler arguments, not executable shell input.
cc -Wall -Wextra -Werror -O2 -shared -fPIC "$source_dir/osk-overlay.c" \
    $(pkg-config --cflags --libs gobject-2.0) -l:libgtk-3.so.0 \
    -o "$root/libgpt-pi-osk-overlay.so.next"
mv -f "$root/libgpt-pi-osk-overlay.so.next" "$root/libgpt-pi-osk-overlay.so"
cat > "$HOME/.local/bin/gpt-pi-keyboard" <<'EOF'
#!/bin/sh
set -eu
module="$HOME/.local/lib/gpt-pi-osk/libgpt-pi-osk-overlay.so"
export GTK_MODULES="${GTK_MODULES:+$GTK_MODULES:}$module"
exec /usr/bin/squeekboard "$@"
EOF
chmod 700 "$HOME/.local/bin/gpt-pi-keyboard"
target="$HOME/.config/autostart/squeekboard.desktop"
if test -f "$target" && ! test -f "$root/squeekboard.desktop.before" &&
   ! grep -Fqx "Exec=$HOME/.local/bin/gpt-pi-keyboard" "$target"; then
    cp "$target" "$root/squeekboard.desktop.before"
fi
sed "s|^Exec=.*|Exec=$HOME/.local/bin/gpt-pi-keyboard|" "$desktop_source" > "$target"
printf '%s\n' 'Keyboard overlay installed for this desktop user; restart its existing keyboard once.'
