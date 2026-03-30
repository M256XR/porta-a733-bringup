#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin

xlog() {
  msg="[xsession] $*"
  echo "$msg"
  [ -c /dev/ttyAS0 ] && printf '%s\n' "$msg" >/dev/ttyAS0 2>/dev/null || true
  [ -w /dev/kmsg ] && printf '<6>%s\n' "$msg" >/dev/kmsg 2>/dev/null || true
}

xlog "start DISPLAY=${DISPLAY:-unset} XAUTHORITY=${XAUTHORITY:-unset}"
sleep 2

if ! xrandr --query >/run/porta-xrandr.out 2>/run/porta-xrandr.err; then
  xlog "xrandr-query-failed"
  sed -n '1,80p' /run/porta-xrandr.err >/dev/ttyAS0 2>/dev/null || true
  while :; do sleep 3600; done
fi

OUT="$(awk '$2=="connected" && $1 ~ /^HDMI-/ {print $1; exit}' /run/porta-xrandr.out)"
[ -n "$OUT" ] || OUT="$(awk '$2=="connected" {print $1; exit}' /run/porta-xrandr.out)"

if [ -z "$OUT" ]; then
  xlog "no-connected-output"
  sed -n '1,120p' /run/porta-xrandr.out >/dev/ttyAS0 2>/dev/null || true
  while :; do sleep 3600; done
fi

xlog "selected-output=$OUT"
if xrandr --output "$OUT" --primary --mode 1920x1080 --rate 60; then
  xlog "forced-mode=1920x1080@60"
elif xrandr --output "$OUT" --primary --mode 1280x720 --rate 60; then
  xlog "forced-mode=1280x720@60"
elif xrandr --output "$OUT" --primary --mode 1440x2560 --rate 50; then
  xlog "forced-mode=1440x2560@50"
else
  xlog "force-mode-failed"
  if xrandr --output "$OUT" --auto; then
    xlog "auto-ok"
  else
    xlog "auto-failed"
  fi
fi

if command -v xsetroot >/dev/null 2>&1; then
  xsetroot -solid '#003b8e' && xlog "xsetroot-ok" || xlog "xsetroot-failed"
fi

while :; do sleep 3600; done
