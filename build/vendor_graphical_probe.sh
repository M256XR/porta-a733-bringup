#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin

vlog() {
  msg="[graphical-probe] $*"
  echo "$msg"
  [ -c /dev/ttyAS0 ] && printf '%s\n' "$msg" >/dev/ttyAS0 2>/dev/null || true
  [ -w /dev/kmsg ] && printf '<6>%s\n' "$msg" >/dev/kmsg 2>/dev/null || true
}

sleep 90

vlog "start"

vlog "ps-begin"
ps -ef 2>/dev/null | grep -E 'sddm|Xorg|Xwayland|kwin|plasmashell' | grep -v grep | while IFS= read -r line; do
  vlog "ps $line"
done
vlog "ps-end"

vlog "x11-socket-begin"
for p in /tmp/.X11-unix /run/sddm /var/run/sddm /var/log/sddm.log; do
  if [ -e "$p" ]; then
    vlog "exists $p"
  else
    vlog "missing $p"
  fi
done
vlog "x11-socket-end"

vlog "x11-socket-list-begin"
for p in /tmp/.X11-unix /tmp/.X*-lock; do
  if [ -e "$p" ]; then
    ls -ld "$p" 2>/dev/null | while IFS= read -r line; do
      vlog "ls $line"
    done
  fi
done
vlog "x11-socket-list-end"

if [ -f /var/log/sddm.log ]; then
  vlog "sddm-log-begin"
  tail -n 80 /var/log/sddm.log 2>/dev/null | while IFS= read -r line; do
    vlog "sddm $line"
  done
  vlog "sddm-log-end"
fi

for p in /var/log/Xorg.0.log /var/log/Xorg.0.log.old /var/log/sddm.log.old; do
  if [ -f "$p" ]; then
    vlog "logfile-begin $p"
    tail -n 80 "$p" 2>/dev/null | while IFS= read -r line; do
      vlog "log $line"
    done
    vlog "logfile-end $p"
  fi
done

if command -v journalctl >/dev/null 2>&1; then
  vlog "journal-sddm-begin"
  journalctl -b -u sddm --no-pager -n 80 2>/dev/null | while IFS= read -r line; do
    vlog "journal $line"
  done
  vlog "journal-sddm-end"
fi

vlog "done"
