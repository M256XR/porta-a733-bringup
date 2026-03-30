#!/bin/sh
# Execute only when "mode set" in /sys/class/hdmi/hdmi/attr/hdmi_source is set to "no".
# Execution logic: First, switch to the "second resolution" in EDID, then --auto back to the preferred resolution.
# Log: /run/hdmi-toggle-once.log
# Usage: /usr/bin/hdmi-toggle-once [force]
# When force is passed: Ignore the current boot lock and the "mode set" check, and force execution once.

exec 1>>/run/hdmi-toggle-once.log 2>&1
echo "=== $(date) === start"; set -x
PATH=/usr/sbin:/usr/bin:/sbin:/bin

serial_log() {
  msg="[hdmi-toggle-once] $*"
  echo "$msg"
  [ -c /dev/ttyAS0 ] && printf '%s\n' "$msg" >/dev/ttyAS0 2>/dev/null || true
  [ -w /dev/kmsg ] && printf '<6>%s\n' "$msg" >/dev/kmsg 2>/dev/null || true
}

find_xauth() {
  find /var/run/sddm /run/sddm /var/lib/sddm -maxdepth 1 -type f 2>/dev/null | head -n1 || true
}

FORCE_ARG="${1:-}"
ATTR_NODE="/sys/class/hdmi/hdmi/attr/hdmi_source"
TRIGGER_MIN_WIDTH="${TRIGGER_MIN_WIDTH:-0}"   # Optional threshold: When >0, the preferred resolution width must be greater than or equal to this value to trigger execution.

# Ensure the script runs only once per boot (unless force is specified).
LOCK=/run/hdmi-toggle-once.lock
if [ "$FORCE_ARG" != "force" ]; then
  [ -e "$LOCK" ] && { serial_log "lock present, skip"; exit 0; }
  : > "$LOCK"
fi
serial_log "start force=${FORCE_ARG:-none}"

# 1) Read the attr, and proceed only if mode set = no (can be bypassed with force).
MODESET=""
if [ -r "$ATTR_NODE" ]; then
  # Parse the 8th column of the output for the fields:| state | ... | enable | mode set | mode info | force |.
  MODESET="$(awk -F'|' '/\| *state *\|/ {gsub(/^ +| +$/,"",$8); print $8; exit}' "$ATTR_NODE" 2>/dev/null || true)"
  echo "mode_set_from_attr=$MODESET"
  serial_log "attr mode_set=$MODESET"
  if [ "$FORCE_ARG" != "force" ]; then
    [ "$MODESET" = "no" ] || { serial_log "mode set != no, skip"; exit 0; }
  fi
else
  echo "attr not found: $ATTR_NODE"
  serial_log "attr missing: $ATTR_NODE"
  [ "$FORCE_ARG" = "force" ] || { serial_log "skip due to missing attr"; exit 0; }
fi

# 2) Wait for SDDM's X:0 and cookie. Under the UEFI boot path, userspace may
# take much longer to reach a usable X session than on the vendor boot flow.
XAUTH=""; i=0
while [ $i -lt 240 ]; do
  XAUTH="$(find_xauth)"
  if [ -n "$XAUTH" ] && env -i PATH="$PATH" DISPLAY=:0 XAUTHORITY="$XAUTH" xrandr --query >/dev/null 2>&1; then
    break
  fi
  if [ $((i % 20)) -eq 0 ]; then
    serial_log "waiting-xauth attempt=$i candidate=${XAUTH:-none}"
  fi
  i=$((i+1)); sleep 0.5
done
[ -n "$XAUTH" ] || { serial_log "no XAUTH after ${i} attempts"; exit 0; }
serial_log "xauth=$XAUTH"
XR='env -i PATH=/usr/sbin:/usr/bin:/sbin:/bin DISPLAY=:0 XAUTHORITY='"$XAUTH"' xrandr'

# 3) Wait for HDMI to be connected (up to approximately 10 seconds).
i=0
while [ $i -lt 20 ]; do
  STAT="$(cat /sys/class/drm/*HDMI*/status 2>/dev/null | head -n1 || true)"
  [ "$STAT" = "connected" ] && break
  i=$((i+1)); sleep 0.5
done
serial_log "connector-status=${STAT:-unknown}"

# 4) Set the output name: first try HDMI-1, and if not connected, fall back to automatic detection.
OUT="HDMI-1"
$XR --query | grep -q "^$OUT connected" || OUT="$($XR --query | awk '$2=="connected"{print $1; exit}')"
[ -n "$OUT" ] || { serial_log "no connected output"; exit 0; }
serial_log "selected-output=$OUT"

# 5) If a trigger threshold is set (optional), execute only when the EDID preferred resolution width is ≥ the threshold.
if [ "$TRIGGER_MIN_WIDTH" -gt 0 ]; then
  PREF="$($XR --query | awk -v o="$OUT" '
    $1==o && $2=="connected"{in=1; next}
    in && NF==0 {exit}
    in && /\+/ {print $1; exit}
  ')"
  if [ -n "$PREF" ]; then
    PREF_W="$(printf "%s" "$PREF" | awk -F'x' '{print $1+0}')"
    echo "PREF=$PREF PREF_W=$PREF_W TRIGGER_MIN_WIDTH=$TRIGGER_MIN_WIDTH"
    serial_log "preferred=$PREF width=$PREF_W trigger_min_width=$TRIGGER_MIN_WIDTH"
    [ "$PREF_W" -ge "$TRIGGER_MIN_WIDTH" ] || { serial_log "below trigger width, skip"; exit 0; }
  fi
fi

# 6) Parse the EDID modes list from the output and extract the second resolution.
MODES="$($XR --query | awk -v o="$OUT" '
  $1==o && $2=="connected"{in=1; next}
  in && NF==0 {exit}
  in && $1 ~ /^[0-9]+x[0-9]+$/ {print $0}
')"
SECOND="$(printf "%s\n" "$MODES" | awk ' !seen[$1]++ { n++; if (n==2){print $1; exit} }')"
[ -n "$SECOND" ] || SECOND="1280x720"
LINE2="$(printf "%s\n" "$MODES" | awk -v r="$SECOND" '$1==r{print; exit}')"
echo "SECOND_LINE=$LINE2"
echo "$LINE2" | grep -Eq '(^|[[:space:]])60(\.[0-9]+)?' && RATE2="60" || RATE2=""
serial_log "second-mode=$SECOND rate=${RATE2:-auto}"

# 7) Switch to the second resolution from the EDID list, then revert to --auto (back to the EDID preferred resolution).
if [ -n "$RATE2" ]; then
  $XR --output "$OUT" --mode "$SECOND" --rate "$RATE2" || $XR --output "$OUT" --mode "$SECOND" || true
else
  $XR --output "$OUT" --mode "$SECOND" || true
fi
sleep 0.3
$XR --output "$OUT" --auto

# 8) Disable DPMS (Display Power Management Signaling) and screensaver to prevent the display from turning off or going into power-saving mode.
env -i PATH="$PATH" DISPLAY=:0 XAUTHORITY="$XAUTH" xset -dpms s off s noblank 2>/dev/null || true

serial_log "done"
echo "=== $(date) === end"
