#!/bin/sh
# Xsetup - run as root before the login dialog appears

exec >>/run/xsetup-hdmi.log 2>&1
PATH=/usr/sbin:/usr/bin:/sbin:/bin

xlog() {
  msg="[xsetup-hdmi] $*"
  echo "$msg"
  [ -c /dev/ttyAS0 ] && printf '%s\n' "$msg" >/dev/ttyAS0 2>/dev/null || true
  [ -w /dev/kmsg ] && printf '<6>%s\n' "$msg" >/dev/kmsg 2>/dev/null || true
}

xlog "start DISPLAY=${DISPLAY:-unset} XAUTHORITY=${XAUTHORITY:-unset}"

if [ -e /sbin/prime-offload ]; then
  xlog "running prime-offload"
  /sbin/prime-offload || true
fi

sleep 2

if ! xrandr --query >/tmp/xsetup-xrandr.out 2>/tmp/xsetup-xrandr.err; then
  xlog "xrandr-query-failed"
  [ -s /tmp/xsetup-xrandr.err ] && sed -n '1,40p' /tmp/xsetup-xrandr.err >/dev/ttyAS0 2>/dev/null || true
  exit 0
fi

OUT="$(awk '$2=="connected" && $1 ~ /^HDMI-/ {print $1; exit}' /tmp/xsetup-xrandr.out)"
[ -n "$OUT" ] || OUT="$(awk '$2=="connected" {print $1; exit}' /tmp/xsetup-xrandr.out)"

if [ -z "$OUT" ]; then
  xlog "no-connected-output"
  sed -n '1,80p' /tmp/xsetup-xrandr.out >/dev/ttyAS0 2>/dev/null || true
  exit 0
fi

xlog "selected-output=$OUT"
PREFERRED="$(awk -v o="$OUT" '$1==o && $2=="connected"{in=1; next} in && NF==0{exit} in && /\+/ {print $1; exit}' /tmp/xsetup-xrandr.out)"
[ -n "$PREFERRED" ] && xlog "preferred=$PREFERRED"

xrandr --output "$OUT" --primary --mode 1440x2560 --rate 50 && {
  xlog "forced-mode=1440x2560@50"
  exit 0
}

xlog "force-mode-failed, trying auto"
xrandr --output "$OUT" --auto && xlog "auto-ok" || xlog "auto-failed"
