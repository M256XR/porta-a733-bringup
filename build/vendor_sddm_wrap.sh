#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin

swlog() {
  msg="[sddm-wrap] $*"
  echo "$msg"
  [ -c /dev/ttyAS0 ] && printf '%s\n' "$msg" >/dev/ttyAS0 2>/dev/null || true
  [ -w /dev/kmsg ] && printf '<6>%s\n' "$msg" >/dev/kmsg 2>/dev/null || true
}

show_file() {
  p="$1"
  if [ -f "$p" ]; then
    swlog "file $p"
    sed 's/^/[sddm-wrap] conf /' "$p" 2>/dev/null | while IFS= read -r line; do
      echo "$line"
      [ -c /dev/ttyAS0 ] && printf '%s\n' "$line" >/dev/ttyAS0 2>/dev/null || true
      [ -w /dev/kmsg ] && printf '<6>%s\n' "$line" >/dev/kmsg 2>/dev/null || true
    done
  else
    swlog "missing $p"
  fi
}

swlog "start args=$*"
swlog "env XDG_VTNR=${XDG_VTNR:-} XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-} DISPLAY=${DISPLAY:-}"

for p in /dev/tty1 /dev/tty7 /sys/class/tty/tty1 /sys/class/tty/tty7; do
  if [ -e "$p" ]; then
    swlog "exists $p"
  else
    swlog "missing $p"
  fi
done

if command -v loginctl >/dev/null 2>&1; then
  swlog "loginctl-seats-begin"
  loginctl list-seats 2>/dev/null | while IFS= read -r line; do
    swlog "seat $line"
  done
  loginctl seat-status seat0 2>/dev/null | while IFS= read -r line; do
    swlog "seat0 $line"
  done
  swlog "loginctl-seats-end"
fi

for p in \
  /etc/sddm.conf \
  /etc/sddm.conf.d/10-porta-x11.conf \
  /usr/lib/sddm/sddm.conf.d/default.conf \
  /usr/lib/sddm/sddm.conf.d/kde_settings.conf
do
  show_file "$p"
done

for p in \
  /usr/bin/porta-xorg-wrap \
  /usr/lib/xorg/Xorg \
  /usr/bin/Xorg \
  /usr/share/sddm/scripts/Xsetup
do
  if [ -e "$p" ]; then
    swlog "exists $p"
  else
    swlog "missing $p"
  fi
done

swlog "exec /usr/bin/sddm"
exec /usr/bin/sddm "$@"
