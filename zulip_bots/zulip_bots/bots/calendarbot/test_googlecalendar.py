import os
import pytest
from datetime import datetime
from zulip_bots.bots.calendarbot.calendarbot import CalendarBotHandler
from zulip_bots.bots.calendarbot.googlecalendar import (
    GcalMeeting,
    authenticate_google,
    AuthenticationError,
    TOKEN_FILE,
)

from google.auth.transport.requests import Request  # type ignore
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


@pytest.fixture
def create_meeting_details():
    sender_email = "testy@testy.com"
    invitees = ["calendarbot2-bot@recurse.zulipchat.com", "rosenblatt.alex@gmail.com"]
    meeting_start = datetime.fromisoformat("2022-12-13T14:18:00-08:00")
    meeting_end = datetime.fromisoformat("2022-12-13T14:38:00-08:00")
    location = "Big White Room"
    name = "Test Meeting name"
    description = "Test Description"
    length_minutes = 30
    meeting_details = CalendarBotHandler.MeetingDetails(
        invitees=invitees,
        meeting_start=meeting_start,
        meeting_end=meeting_end,
        description=description,
        location=location,
        sender_email=sender_email,
        length_minutes=length_minutes,
        name=name,
    )
    return meeting_details


def test_gcal_meeting_summary_parsing(create_meeting_details):
    gcal_meeting = GcalMeeting(create_meeting_details)
    assert create_meeting_details.name == gcal_meeting.name
    assert create_meeting_details.meeting_start == datetime.fromisoformat(
        gcal_meeting.meeting_start
    )
    assert create_meeting_details.meeting_end == datetime.fromisoformat(gcal_meeting.meeting_end)
    assert create_meeting_details.name == gcal_meeting.name


def test_gcal_meeting_invitee_parsing(create_meeting_details):
    gcal_meeting = GcalMeeting(create_meeting_details)
    attendees = [{"email": invitee} for invitee in create_meeting_details.invitees]
    attendees.append({"email": create_meeting_details.sender_email})
    assert gcal_meeting.attendees == attendees


def test_create_gcal_event(create_meeting_details):
    gcal_meeting = GcalMeeting(create_meeting_details)
    results = gcal_meeting.create_gcal_event()
    assert results["summary"] == gcal_meeting.name
    assert results["location"] == gcal_meeting.location
    assert results["description"] == gcal_meeting.description
    assert results["start"]["dateTime"] == gcal_meeting.meeting_start
    assert results["end"]["dateTime"] == gcal_meeting.meeting_end
    assert results["attendees"] == gcal_meeting.attendees


# in progress
# def test_authenticate_google_has_creds(monkeypatch):
#     monkeypatch.setattr(os.path, "exists", lambda: True)
#     monkeypatch.setattr(Credentials, "from_authorized_user_file", lambda: True)
#     monkeypatch.setattr(Credentials, "valid", lambda: True)
#     monkeypatch.setattr(Credentials, "expired", lambda: False)
#     monkeypatch.setattr(Credentials, "refresh_token", lambda: False)
#     monkeypatch.setattr(InstalledAppFlow, "from_client_secrets_file", lambda: True)
#     TOKEN_FILE = "tmpfile.json"
#     with pytest.raises(AuthenticationError):
#         authenticate_google()
