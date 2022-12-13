import pytest
from zulip_bots.bots.calendarbot.calendarbot import CalendarBotHandler
from zulip_bots.bots.calendarbot.googlecalendar import GcalMeeting


@pytest.fixture
def create_meeting_details():
    sender_id=3434
    invitees=['test@test.com','rosentest@test.com']
    meeting_start = 
    return CalendarBotHandler.MeetingDetails(self.MeetingDetails(sender_id=sender_id,
                invitees=invitees,
                meeting_start=meeting_start,
                meeting_end=meeting_end,
                length_minutes=length_minutes,
                name=name,summary=summary)


def test_gcal_meeting_parsing():
    assert GcalMeeting()
