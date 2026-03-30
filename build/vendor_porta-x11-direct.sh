#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin

log() {
  msg="[xdirect] $*"
  echo "$msg"
  [ -c /dev/ttyAS0 ] && printf '%s\n' "$msg" >/dev/ttyAS0 2>/dev/null || true
  [ -w /dev/kmsg ] && printf '<6>%s\n' "$msg" >/dev/kmsg 2>/dev/null || true
}

log "start"

for p in /dev/dri /dev/tty1 /sys/class/drm; do
  if [ -e "$p" ]; then
    log "exists $p"
  else
    log "missing $p"
  fi
done

if [ -d /sys/class/drm ]; then
  for n in /sys/class/drm/*; do
    [ -e "$n" ] || continue
    b="$(basename "$n")"
    [ -f "$n/status" ] && log "drm-status $b=$(cat "$n/status" 2>/dev/null || echo '?')"
    [ -f "$n/enabled" ] && log "drm-enabled $b=$(cat "$n/enabled" 2>/dev/null || echo '?')"
  done
fi

mkdir -p /run
: >/run/porta-Xorg.log
tail -F /run/porta-Xorg.log >/dev/ttyAS0 2>/dev/null &
TAILPID=$!

trap 'kill "$TAILPID" 2>/dev/null || true' EXIT INT TERM

rm -f /tmp/.X0-lock
log "launching xinit"
xinit /usr/bin/porta-x11-session -- /usr/bin/Xorg :0 vt1 -nolisten tcp -verbose 3 -logfile /run/porta-Xorg.log
RC=$?
log "xinit-exit=$RC"
sleep 1
exit 0
