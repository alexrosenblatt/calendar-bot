from __future__ import print_function

import logging
import os.path
from dataclasses import dataclass
from datetime import datetime, time

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dataclasses import dataclass

logging.basicConfig(
    filename="zulip_bots/zulip_bots/bots/calendarbot/calendarbot.log",
    encoding="utf-8",
    level=logging.DEBUG,
)

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar"]

from google.oauth2 import service_account

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS_FILE = "zulip_bots/zulip_bots/bots/calendarbot/creds.json"
BOT_CALENDAR_ID = (
    "5edeaa7e7808543c6f5b1f64433d135e618cc3cad5d2c2f2df2b452c81957459@group.calendar.google.com"
)


def authenticate_google():
    # TODO we need to prevent the authenticate refresh flow from running for end users

    try:
        global creds
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists("token.json"):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            logging.debug("Cred token found. Using existing credentials")
        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
                logging.debug("Credentials expired - requesting a refresh of authentication")
            else:
                logging.debug("No credentials found - Initiating authentication flow")
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                creds = flow.run_local_server(port=8080)
                creds = creds
            # Save the credentials for the next run
            with open("token.json", "w") as token:
                token.write(creds.to_json())
    except:
        logging.exception("Error occurred during google authentication.")
        raise (AuthenticationError)


@dataclass
class GcalMeeting:
    def __init__(self, meeting_details) -> None:
        self.creds = self.authenticate_with_token()
        self.name: str = meeting_details.name
        self.summary: str = meeting_details.summary
        self.meeting_start: str = meeting_details.meeting_start.isoformat()
        self.meeting_end: str = meeting_details.meeting_end.isoformat()
        self.attendees: list[dict[str, str]] = [
            {"email": invitee} for invitee in meeting_details.invitees
        ]
        self.calendar = build("calendar", "v3", credentials=self.creds)

        self.parsed_details = self.create_gcal_event()

    def authenticate_with_token(self):
        try:
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
        except:
            logging.debug("Cred file cannot be loaded.")
            raise AuthenticationError
        return creds

    def send_event(self):
        try:
            event = (
                self.calendar.events()
                .insert(
                    calendarId=BOT_CALENDAR_ID,
                    body=self.parsed_details,
                    sendUpdates="all",
                )
                .execute()
            )
            logging.debug("Event created: %s" % (event.get("htmlLink")))

        except HttpError as error:
            logging.exception("An error occurred: %s" % error)

    def create_gcal_event(self) -> dict:
        return {
            "summary": self.name,
            "location": "Remote Recurse",
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


class AuthenticationError(Exception):
    """Raised when google calendar authentication cannot be completed."""

    pass
