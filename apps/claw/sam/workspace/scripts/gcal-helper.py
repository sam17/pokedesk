#!/usr/bin/env python3
"""Google Calendar helper for Dobby. Supports multiple accounts."""

import sys
import json
import argparse
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build


def get_workspace_service():
    """Service account for soumyadeep@dashverse.ai"""
    creds = service_account.Credentials.from_service_account_file(
        '/home/node/.openclaw/google-service-account.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        subject='soumyadeep@dashverse.ai'
    )
    return build('calendar', 'v3', credentials=creds)


def get_personal_service():
    """OAuth for personal Gmail (requires token setup)"""
    from google.oauth2.credentials import Credentials
    token_path = '/home/node/.openclaw/gcal-personal-token.json'
    creds = Credentials.from_authorized_user_file(token_path,
        scopes=['https://www.googleapis.com/auth/calendar'])
    return build('calendar', 'v3', credentials=creds)


def get_service(account):
    if account == 'work':
        return get_workspace_service()
    elif account == 'personal':
        return get_personal_service()
    else:
        raise ValueError(f"Unknown account: {account}. Use 'work' or 'personal'")


def list_calendars(args):
    service = get_service(args.account)
    result = service.calendarList().list().execute()
    for cal in result.get('items', []):
        print(f"{cal['summary']:50s} {cal['id']}")


def list_events(args):
    service = get_service(args.account)
    now = datetime.now(timezone.utc)

    if args.date:
        start = datetime.strptime(args.date, '%Y-%m-%d').replace(tzinfo=timezone.utc)
        end = start + timedelta(days=1)
    else:
        start = now
        end = now + timedelta(days=int(args.days))

    time_min = start.isoformat()
    time_max = end.isoformat()

    calendar_id = args.calendar or 'primary'
    result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = result.get('items', [])
    if not events:
        print('No events found.')
        return

    for event in events:
        start_str = event['start'].get('dateTime', event['start'].get('date', ''))
        end_str = event['end'].get('dateTime', event['end'].get('date', ''))
        summary = event.get('summary', '(no title)')
        print(f"{start_str:25s} - {end_str:25s}  {summary}")
        if args.verbose and event.get('description'):
            print(f"    {event['description'][:200]}")


def create_event(args):
    service = get_service(args.account)
    calendar_id = args.calendar or 'primary'

    event_body = {
        'summary': args.title,
        'start': {'dateTime': args.start, 'timeZone': args.timezone},
        'end': {'dateTime': args.end, 'timeZone': args.timezone},
    }
    if args.description:
        event_body['description'] = args.description

    event = service.events().insert(calendarId=calendar_id, body=event_body).execute()
    print(f"Created: {event.get('htmlLink')}")


def search_events(args):
    service = get_service(args.account)
    now = datetime.now(timezone.utc)
    time_min = (now - timedelta(days=int(args.past_days))).isoformat()
    time_max = (now + timedelta(days=int(args.future_days))).isoformat()

    calendar_id = args.calendar or 'primary'
    result = service.events().list(
        calendarId=calendar_id,
        timeMin=time_min,
        timeMax=time_max,
        q=args.query,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = result.get('items', [])
    if not events:
        print('No matching events.')
        return

    for event in events:
        start_str = event['start'].get('dateTime', event['start'].get('date', ''))
        summary = event.get('summary', '(no title)')
        print(f"{start_str:25s}  {summary}")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Google Calendar helper')
    parser.add_argument('--account', default='work', choices=['work', 'personal'],
                        help='Which account (work=dashverse.ai, personal=gmail)')
    sub = parser.add_subparsers(dest='command')

    # calendars
    sub.add_parser('calendars', help='List calendars')

    # events
    ev = sub.add_parser('events', help='List events')
    ev.add_argument('--date', help='Specific date (YYYY-MM-DD)')
    ev.add_argument('--days', default='7', help='Days ahead (default 7)')
    ev.add_argument('--calendar', help='Calendar ID (default: primary)')
    ev.add_argument('--verbose', '-v', action='store_true')

    # create
    cr = sub.add_parser('create', help='Create event')
    cr.add_argument('--title', required=True)
    cr.add_argument('--start', required=True, help='ISO datetime')
    cr.add_argument('--end', required=True, help='ISO datetime')
    cr.add_argument('--description', default='')
    cr.add_argument('--calendar', help='Calendar ID')
    cr.add_argument('--timezone', default='Asia/Kolkata')

    # search
    se = sub.add_parser('search', help='Search events')
    se.add_argument('query')
    se.add_argument('--past-days', default='30')
    se.add_argument('--future-days', default='30')
    se.add_argument('--calendar', help='Calendar ID')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == 'calendars':
        list_calendars(args)
    elif args.command == 'events':
        list_events(args)
    elif args.command == 'create':
        create_event(args)
    elif args.command == 'search':
        search_events(args)
