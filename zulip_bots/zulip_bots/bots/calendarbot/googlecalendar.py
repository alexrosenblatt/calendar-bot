import logging
import os.path
from dataclasses import dataclass

# TODO: Google packages (google-api-python-client, google-auth-oauthlib) need to be installed into venv
from google.auth.transport.requests import Request  # type ignore
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


logging.basicConfig(
    filename="zulip_bots/zulip_bots/bots/calendarbot/calendarbot.log",
    encoding="utf-8",
    level=logging.DEBUG,
)


# If modifying these scopes, delete the file token.json
SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDS_FILE = "./creds.json"
BOT_CALENDAR_ID = (
    "5edeaa7e7808543c6f5b1f64433d135e618cc3cad5d2c2f2df2b452c81957459@group.calendar.google.com"
)
TOKEN_FILE = "token.json"


def authenticate_google():
    # TODO: We need to prevent the authenticate refresh flow from running for end users
    # TODO: write tests for this @Alex

    try:
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first
        # time.
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file("token.json", SCOPES)
            logging.debug("Cred token found. Using existing credentials")
        # If there are no (valid) credentials available, let the user log in.
        else:
            logging.debug("Cred token not found. Starting auth or refresh")
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                logging.debug("Cred token not found. Starting refresh")
                creds.refresh(Request())
                logging.debug("Credentials expired - requesting a refresh of authentication")
            else:
                logging.debug("No credentials found - Initiating authentication flow")
                flow = InstalledAppFlow.from_client_secrets_file(CREDS_FILE, SCOPES)
                creds = flow.run_local_server(port=8080)
            # Save the credentials for the next run

            with open(TOKEN_FILE, "w+") as token:

                token.write(creds.to_json())
    except:
        logging.exception("Error occurred during google authentication.")
        raise (AuthenticationError)


@dataclass
class GcalMeeting:
    def __init__(self, meeting_details) -> None:
        self.name: str = meeting_details.name
        self.location = meeting_details.location
        self.description: str = meeting_details.description
        self.meeting_start: str = meeting_details.meeting_start.isoformat()
        self.meeting_end: str = meeting_details.meeting_end.isoformat()
        # TODO: Add sender_email to attendee list
        self.attendees: list[dict[str, str]] = [
            {"email": invitee} for invitee in meeting_details.invitees
        ]
        # add sender email back into invitee list
        self.attendees.append({"email": meeting_details.sender_email})  # TODO test this


    def auth_and_create_google_calendar(self):
        creds = self.authenticate_with_token()
        self.calendar = build("calendar", "v3", credentials=creds)

        self.parsed_details = self.create_gcal_event()

    def authenticate_with_token(self):
        try:

            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

            return creds
        except:
            logging.debug("Cred file cannot be loaded.")
            raise AuthenticationError

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
            "location": self.location,
            "description": self.description,
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
    """
    Raised when google calendar authentication cannot be completed.
    """

    ...
