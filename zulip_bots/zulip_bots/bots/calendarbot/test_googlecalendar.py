import pytest

from datetime import datetime
from zulip_bots.bots.calendarbot.calendarbot import CalendarBotHandler
from zulip_bots.bots.calendarbot.googlecalendar import GcalMeeting


@pytest.fixture
def meeting_details_happy_path():
    sender_id = 3434
    invitees = ["calendarbot2-bot@recurse.zulipchat.com", "rosenblatt.alex@gmail.com"]
    meeting_start = datetime.fromisoformat("2022-12-13T14:18:00-08:00")
    meeting_end = datetime.fromisoformat("2022-12-13T14:38:00-08:00")
    name = "test name"
    summary = "test summary"
    length_minutes = 30
    meeting_details = CalendarBotHandler.MeetingDetails(
        sender_id=sender_id,
        invitees=invitees,
        meeting_start=meeting_start,
        meeting_end=meeting_end,
        length_minutes=length_minutes,
        name=name,
        summary=summary,
    )
    return meeting_details


@pytest.fixture
def test_good_token():
    token = {
        "token": "ya29.a0AeTM1idtetn_pW3fI_6snX_cf2uw2fjsu03eeuT7tjWysBkUeYThUErHXFC9JdGiL9pimloQs9I3xBQeZKnlWsQ7VcHISM9z7A0hPeIzg7z-2vrYIGLYhGSfj3lPukk_b2T6Q9Mf2kmaFw6B7OAJdx5nIJbSaCgYKAcASARESFQHWtWOmblXwWWFlYrPyid0vkY72Tw0163",
        "refresh_token": "1//06RF9T10KlaOCCgYIARAAGAYSNwF-L9IrYZr2-9geMfDxRm3Wzy1lxSQKSlzuFh-XLUazYrn3vuI4SMzr__1250UY9SVJta_dkQQ",
        "token_uri": "https://oauth2.googleapis.com/token",
        "client_id": "967750785532-e08f0o15hadakh8rvufda6rbrueftlht.apps.googleusercontent.com",
        "client_secret": "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",
        "scopes": ["https://www.googleapis.com/auth/calendar"],
        "expiry": "2022-12-13T21:57:40.737432Z",
    }
    return token


@pytest.fixture
def test_empty_creds():
    token = {}
    return token


def test_gcal_meeting_summary_parsing(meeting_details_happy_path):
    gcal_meeting = GcalMeeting(meeting_details_happy_path)
    assert meeting_details_happy_path.summary == gcal_meeting.summary
    assert meeting_details_happy_path.meeting_start == datetime.fromisoformat(
        gcal_meeting.meeting_start
    )
    assert meeting_details_happy_path.meeting_end == datetime.fromisoformat(
        gcal_meeting.meeting_end
    )
    assert meeting_details_happy_path.name == gcal_meeting.name


def test_gcal_meeting_invitee_parsing(meeting_details_happy_path):
    gcal_meeting = GcalMeeting(meeting_details_happy_path)
    attendees = [{"email": invitee} for invitee in meeting_details_happy_path.invitees]
    assert gcal_meeting.attendees == attendees


def test_no_token_found(meeting_details_happy_path):
    TOKEN_FILE = "tokdden.json"
    print("poop")
    try:
        gcal_meeting = GcalMeeting(meeting_details_happy_path)
        creds = gcal_meeting.authenticate_with_token()
        print("poop")
        assert creds == Nonex
    except:
        print("poop")
        pytest.raises(Exception)
