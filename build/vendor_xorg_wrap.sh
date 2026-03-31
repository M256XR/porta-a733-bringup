#!/bin/sh
PATH=/usr/sbin:/usr/bin:/sbin:/bin

xwlog() {
  msg="[xorg-wrap] $*"
  echo "$msg"
  [ -c /dev/ttyAS0 ] && printf '%s\n' "$msg" >/dev/ttyAS0 2>/dev/null || true
  [ -w /dev/kmsg ] && printf '<6>%s\n' "$msg" >/dev/kmsg 2>/dev/null || true
}

xwlog "start args=$*"

if [ -x /usr/lib/xorg/Xorg ]; then
  xwlog "exec /usr/lib/xorg/Xorg -logverbose 7 -verbose 7"
  exec /usr/lib/xorg/Xorg "$@" -logverbose 7 -verbose 7 >>/dev/ttyAS0 2>&1
fi

if [ -x /usr/bin/Xorg ]; then
  xwlog "exec /usr/bin/Xorg -logverbose 7 -verbose 7"
  exec /usr/bin/Xorg "$@" -logverbose 7 -verbose 7 >>/dev/ttyAS0 2>&1
fi

xwlog "missing-xorg-binary"
exit 127
