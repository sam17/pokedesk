# TOOLS.md - Local Notes

## Google Calendar

Script: `python3 scripts/gcal-helper.py`

| Command | Example |
|---------|---------|
| List calendars | `python3 scripts/gcal-helper.py --account work calendars` |
| Today's events | `python3 scripts/gcal-helper.py --account work events --date 2026-03-25` |
| Next 7 days | `python3 scripts/gcal-helper.py --account work events --days 7` |
| Search events | `python3 scripts/gcal-helper.py --account work search "topic"` |
| Create event | `python3 scripts/gcal-helper.py --account work create --title "X" --start "2026-03-26T10:00:00" --end "2026-03-26T11:00:00"` |

Accounts: `work` = soumyadeep@dashverse.ai, `personal` = not yet configured

## Obsidian Notes

Sam's Obsidian vault **is** the `notes/` folder (`~/.openclaw/workspace/notes`) — a real Dropbox-synced directory (same Maestral mechanism as `~/Dropbox`). Direct filesystem access.

| Action | Command |
|--------|---------|
| List notes | `ls notes/` |
| Read a note | `cat notes/filename.md` |
| Search notes | `grep -rl "search term" notes/` |
| Create note | Write .md file to `notes/` |

Changes sync **two-way via Dropbox (Maestral), usually within seconds** to Sam's Obsidian on his laptop. It is NOT a 5-minute poll, NOT a background job you trigger, and NOT tied to a Git commit — just write the `.md` file and it propagates. (If a change looks stuck for more than a few minutes, Maestral may be paused; a watchdog auto-restarts it.)
