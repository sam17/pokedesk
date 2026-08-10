---
name: gcal-helper
description: Access Sam's Google Calendar — list events, search, create meetings for work (dashverse.ai) account
---

# Google Calendar Helper

A Python script at `scripts/gcal-helper.py` that provides read/write access to Google Calendar via service account.

## Commands

### List calendars
```bash
python3 scripts/gcal-helper.py --account work calendars
```

### List events for a specific date
```bash
python3 scripts/gcal-helper.py --account work events --date YYYY-MM-DD
```

### List events for next N days
```bash
python3 scripts/gcal-helper.py --account work events --days 7
```

### List events with descriptions (verbose)
```bash
python3 scripts/gcal-helper.py --account work events --date YYYY-MM-DD --verbose
```

### Search events by keyword
```bash
python3 scripts/gcal-helper.py --account work search "meeting topic" --past-days 30 --future-days 30
```

### Create an event
```bash
python3 scripts/gcal-helper.py --account work create --title "Meeting Title" --start "2026-03-26T10:00:00" --end "2026-03-26T11:00:00" --description "Optional description" --timezone "Asia/Kolkata"
```

### Target a specific calendar
Add `--calendar CALENDAR_ID` to any command. Default is primary calendar.

## Accounts

| Account flag | Email | Auth method |
|---|---|---|
| `--account work` | soumyadeep@dashverse.ai | Service account (always works) |
| `--account personal` | Personal Gmail | Not yet configured |

## Notes

- Default timezone: Asia/Kolkata
- Sam's primary work calendar ID: `soumyadeep@dashverse.ai`
- Use ISO format for dates/times
- The `--verbose` flag shows event descriptions
