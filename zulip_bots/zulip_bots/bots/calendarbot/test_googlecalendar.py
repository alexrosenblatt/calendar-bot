import pytest
from datetime import datetime
from zulip_bots.bots.calendarbot.calendarbot import CalendarBotHandler
from zulip_bots.bots.calendarbot.googlecalendar import GcalMeeting


@pytest.fixture
def create_meeting_details():
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
        description=description,
        location=location,
        sender_email=sender_email,
        length_minutes=length_minutes,
        name=name,
        summary=summary,
    )
    return meeting_details


def test_gcal_meeting_summary_parsing(create_meeting_details):
    gcal_meeting = GcalMeeting(create_meeting_details)
    assert create_meeting_details.summary == gcal_meeting.summary
    assert create_meeting_details.meeting_start == datetime.fromisoformat(
        gcal_meeting.meeting_start
    )
    assert create_meeting_details.meeting_end == datetime.fromisoformat(gcal_meeting.meeting_end)
    assert create_meeting_details.name == gcal_meeting.name


def test_gcal_meeting_invitee_parsing(create_meeting_details):
    gcal_meeting = GcalMeeting(create_meeting_details)
    attendees = [{"email": invitee} for invitee in create_meeting_details.invitees]
    assert gcal_meeting.attendees == attendees
