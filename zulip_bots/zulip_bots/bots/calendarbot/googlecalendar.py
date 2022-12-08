from __future__ import print_function

import datetime
import os.path
from dataclasses import dataclass
from datetime import datetime, time

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "python-zulip-api/zulip_bots/zulip_bots/bots/calendarbot/creds.json"


def send_google_invite(meeting_details):
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(SERVICE_ACCOUNT_FILE, SCOPES)
            creds = flow.run_local_server(port=8080)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        calendar = build("calendar", "v3", credentials=creds)
        print(meeting_details.invitees)
        attendee = {"email": invitee for invitee in meeting_details.invitees}
        print(attendee)
        # Call the Calendar API
        event = {
            "summary": meeting_details.name,
            "location": "800 Howard St., San Francisco, CA 94103",
            "description": meeting_details.summary,
            "start": {
                "dateTime": meeting_details.meeting_start.isoformat(),
            },
            "end": {
                "dateTime": meeting_details.meeting_end.isoformat(),
            },
            "attendees": [
                attendee,
            ],
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }

        event = (
            calendar.events()
            .insert(
                calendarId="5edeaa7e7808543c6f5b1f64433d135e618cc3cad5d2c2f2df2b452c81957459@group.calendar.google.com",
                body=event,
                sendUpdates="all",
            )
            .execute()
        )
        print("Event created: %s" % (event.get("htmlLink")))

    except HttpError as error:
        print("An error occurred: %s" % error)
