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
  xwlog "exec /usr/lib/xorg/Xorg"
  exec /usr/lib/xorg/Xorg "$@"
fi

if [ -x /usr/bin/Xorg ]; then
  xwlog "exec /usr/bin/Xorg"
  exec /usr/bin/Xorg "$@"
fi

xwlog "missing-xorg-binary"
exit 127
