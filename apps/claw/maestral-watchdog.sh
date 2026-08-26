#!/bin/bash
# Restart Maestral if its sync has silently stalled (process can stay alive while paused,
# which defeats systemd Restart=on-failure). Log-based because the CLI cannot see the
# systemd `maestral start -f` daemon. Installed 2026-08-24.
LOG="$HOME/.cache/maestral/maestral.log"
WLOG="$HOME/.cache/maestral/watchdog.log"
STAMP="$HOME/.cache/maestral/.watchdog-last-restart"
now=$(date +%s)
log(){ echo "$(date +%F %T) $*" >> "$WLOG"; }

do_restart(){
  if [ -f "$STAMP" ]; then
    since=$(( now - $(cat "$STAMP" 2>/dev/null || echo 0) ))
    [ "$since" -lt 900 ] && { log "SKIP (restarted ${since}s ago) reason=$1"; exit 0; }
  fi
  echo "$now" > "$STAMP"
  log "RESTART maestral reason=$1"
  sudo systemctl restart maestral
  exit 0
}

systemctl is-active --quiet maestral || do_restart "service-inactive"
[ -f "$LOG" ] || { log "no-logfile"; exit 0; }

last=$(grep -aE "Up to date|Syncing|Paused|Sync aborted| ERROR" "$LOG" | tail -1)
age=$(( now - $(stat -c %Y "$LOG") ))
case "$last" in
  *Paused*|*"Sync aborted"*|*" ERROR"*) do_restart "stuck:${last##*: }";;
esac
# stuck mid-sync / connecting: last state is transient but log has not advanced
if echo "$last" | grep -q "Syncing"; then
  [ "$age" -gt 1800 ] && do_restart "stuck-syncing-${age}s"
fi
exit 0
