from __future__ import print_function

import logging
import os.path
from dataclasses import dataclass
from datetime import datetime, time

from google.auth.transport.requests import Request
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logging.basicConfig(
    filename="zulip_bots/zulip_bots/bots/calendarbot/calendarbot.log",
    encoding="utf-8",
    level=logging.DEBUG,
)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/calendar"]
SERVICE_ACCOUNT_FILE = "zulip_bots/zulip_bots/bots/calendarbot/creds.json"
BOT_CALENDAR_ID = (
    "5edeaa7e7808543c6f5b1f64433d135e618cc3cad5d2c2f2df2b452c81957459@group.calendar.google.com"
)


class GoogleEvent:
    def __init__(self, meeting_details) -> None:
        self.authenticate_google()
        self.name = meeting_details.name
        self.summary = meeting_details.summary
        self.meeting_start = meeting_details.meeting_start.isoformat()
        self.meeting_end = meeting_details.meeting_end.isoformat()
        self.attendees = [{"email": invitee} for invitee in meeting_details.invitees]
        self.creds

    def authenticate_google(self):
        try:
            self.creds = None
            # The file token.json stores the user's access and refresh tokens, and is
            # created automatically when the authorization flow completes for the first
            # time.
            if os.path.exists("token.json"):
                self.creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            # If there are no (valid) credentials available, let the user log in.
            if not self.creds or not self.creds.valid:
                if self.creds and self.creds.expired and self.creds.refresh_token:
                    self.creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(SERVICE_ACCOUNT_FILE, SCOPES)
                    creds = flow.run_local_server(port=8080)
                    self.creds = creds
                # Save the credentials for the next run
                with open("token.json", "w") as token:
                    token.write(self.creds.to_json())
        except:
            logging.exception("Error occurred during google authentication.")

    def send_google_invite(self):
        try:
            calendar = build("calendar", "v3", credentials=self.creds)

            self.new_method()

            event = (
                calendar.events()
                .insert(
                    calendarId=BOT_CALENDAR_ID,
                    body=event,
                    sendUpdates="all",
                )
                .execute()
            )
            logging.debug("Event created: %s" % (event.get("htmlLink")))

        except HttpError as error:
            logging.exception("An error occurred: %s" % error)

    def new_method(self):
        event = {
            "summary": self.name,
            "location": "800 Howard St., San Francisco, CA 94103",
            "description": self.summary,
            "start": {
                "dateTime": self.meeting_start,
            },
            "end": {
                "dateTime": self.meeting_end,
            },
            "attendees": self.attendees,
            "reminders": {
                "useDefault": False,
                "overrides": [
                    {"method": "email", "minutes": 24 * 60},
                    {"method": "popup", "minutes": 10},
                ],
            },
        }
