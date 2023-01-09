import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from re import search
from typing import Any, Dict, List, Optional, Union

from ics import Attendee, Calendar, Event

from zulip_bots.bots.calendarbot.googlecalendar import AuthenticationError
from zulip_bots.bots.calendarbot.googlecalendar import GcalMeeting as GcalMeeting
from zulip_bots.bots.calendarbot.googlecalendar import authenticate_google
from zulip_bots.lib import BotHandler

logging.basicConfig(
    filename="zulip_bots/zulip_bots/bots/calendarbot/calendarbot.log",
    encoding="utf-8",
    level=logging.DEBUG,
)


# TODO: Take this from environment variables in the future
BOT_REGEX = "(.*\*\*.*|.*bot.*)"
TIME_FORMAT = "^(<time).*(>)$"
DEFAULT_EVENT_DURATION = 30
VIRTUAL_RC = "https://recurse.rctogether.com/"


class MeetingTypes(Enum):
    PAIRING = 1
    COFFEE_CHAT = 2


class CalendarBotHandler(object):
    """
    This bot fucking loves meetings.
    """

    @dataclass
    class MeetingDetails:
        name: str
        location: str
        description: str
        meeting_start: datetime
        meeting_end: datetime
        length_minutes: int
        sender_email: str
        invitees: list

    def initialize(self, bot_handler: BotHandler) -> None:
        storage = bot_handler.storage

        # Add key values in the bot_handler storage
        if not storage.contains("confirmation"):
            storage.put("confirmation", None)
        if not storage.contains("starttime"):
            storage.put("starttime", None)
        if not storage.contains("duration"):
            storage.put("duration", 0)
        if not storage.contains("meeting_type"):
            storage.put("meeting_type", None)

    def usage(self) -> str:
        return (
            "Calendar Bot creates a calendar meeting for all participants on chat. "
            "Enter a Zulip global time `<time` and then a duration in minutes (e.g. 60 for 1 hour). "
            "Default event duration is 30 mins and default email addresses are from user accounts. "
            "Optionally, append 'coffee' or 'pairing' to customize the meeting type."
        )

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        storage = bot_handler.storage
        confirmation = storage.get("confirmation")
        starttime = storage.get("starttime")
        duration = storage.get("duration")
        meeting_type = storage.get("meeting_type")

        # TODO: Instantiating Calendar here for now due to bug when trying to move it to init, works but may cause issues in future
        cal = Calendar()

        # Parse the initial message containing the event time and duration info
        if confirmation is None and starttime is None:
            bot_response = self.parse_first_message(message, bot_handler)
            bot_handler.send_reply(message, bot_response)

        # Parse the second message for the meeting info confirmation
        elif confirmation is None and starttime:
            try:
                # Q: Passing in values vs another request to bot_handler
                bot_response = self.parse_second_message(
                    message, bot_handler, starttime, cal, duration, meeting_type
                )
            except:
                # TODO: Target more specific errors
                bot_response = f"Could not parse confirmation message: '{message['content']}'. Please message CalendarBot with 'Y' / 'N' to confirm <time:{starttime}>"
                logging.exception("Message parsing failed")

            bot_handler.send_reply(message, bot_response)

    def message_content_helper(self, message: Dict[str, Any]) -> List[str]:
        # Split the message string to CalendarBot
        args = message["content"].lower().split()

        # Filter out any arguments that could be related to the bot name. This occurs when there are more than 2 users in the chat.
        return [x for x in args if not search(BOT_REGEX, x)]

    def parse_first_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> str:
        bot_handler.storage.put("confirmation", None)

        filtered_args = self.message_content_helper(message)
        num_args = len(filtered_args)
        duration = DEFAULT_EVENT_DURATION

        def set_duration(duration):
            try:
                bot_handler.storage.put("duration", int(duration))
            except:
                return (
                    f"Could not parse duration input {filtered_args[1]}"  # TODO return error with
                )

        def set_meeting_type(meeting_type):
            try:
                bot_handler.storage.put("type", int(meeting_type))
            except:
                return f"Could not parse duration input {filtered_args[1]}"

        # Validate args Zulip global time and duration
        if not num_args or filtered_args[0] == "help":
            return self.usage()
        elif filtered_args[0] == "auth":
            authenticate_google()
            return "Authenticating Google token..."
        elif num_args > 3:
            return f"Expected at most 3 arguments, received {num_args}"

        if not search(TIME_FORMAT, filtered_args[0]):
            return f"Could not parse '{message['content']}'. Please pass in a Zulip global time `<time`"

        if num_args == 2:
            set_duration(filtered_args[1])

        elif num_args == 3:
            set_duration(filtered_args[1])
            set_meeting_type(filtered_args[2])

        time = filtered_args[0].replace("<time:", "").replace(">", "")
        bot_handler.storage.put("starttime", time)

        confirm_message = f"Create a meeting at {filtered_args[0]} for {duration} mins? (Y / N)"

        return confirm_message

    # TODO: Check what occurs when a different sender pings bot
    def parse_second_message(
        self,
        message: Dict[str, Any],
        bot_handler: BotHandler,
        starttime: str,
        cal: Calendar,
        meeting_type: MeetingTypes = MeetingTypes.COFFEE_CHAT,
        duration: Union[str, int] = DEFAULT_EVENT_DURATION,
    ) -> str:
        """
        Process confirmation for meeting details in temporary bot_handler storage
        """

        filtered_args = self.message_content_helper(message)
        confirmation = filtered_args[0]

        def set_meeting_title(meeting_type):
            recipient_names = []
            for names in message["display_recipient"]:
                recipient_names.append(names)
            if meeting_type == MeetingTypes.COFFEE_CHAT:
                meeting_name = f"Coffee Chat with {recipient_names}"
            elif meeting_type == MeetingTypes.PAIRING:
                meeting_name = f"Pairing with {recipient_names}"
            else:
                meeting_name = f"Meeting with {recipient_names}"
            return meeting_name

        meeting_name = set_meeting_title(meeting_type)

        if confirmation == "y":
            duration = int(duration)
            meeting_start, meeting_end = self.parse_datetime_input(starttime, duration)
            meeting_details = self.create_meeting_details(
                meeting_start,
                meeting_end,
                message["sender_email"],
                message["display_recipient"],
                duration,
                name=meeting_name,
            )

            # Create event ics file for download
            self.create_ics_event(meeting_details, cal)
            self.send_event_file(message, bot_handler, cal)
            # Create Google event
            google_response = self.send_google_event_invite(meeting_details)
            # Remove event details from storage
            self.clear_storage(bot_handler)

            return google_response

        elif confirmation == "n":
            self.clear_storage(bot_handler)

            return "Got it! I will remove any saved event data."

        else:
            raise TypeError

    def parse_datetime_input(self, starttime: str, duration: int) -> tuple[datetime, datetime]:
        """
        Converts Zulip global timepicker into a python datetime object
        """

        meeting_start = datetime.fromisoformat(starttime)
        meeting_end = meeting_start + timedelta(minutes=duration)

        return meeting_start, meeting_end

    def create_meeting_details(
        self,
        meeting_start: datetime,
        meeting_end: datetime,
        sender_email: str,
        recipients: List[dict],
        duration: int,
        name,
    ) -> MeetingDetails:
        description = "TEST Event Description"

        # Parse out id and email from recipients
        parsed_recipients = list(
            map(lambda recipient: (recipient["id"], recipient["email"]), recipients)
        )
        # Remove sender and bot from recipient list
        invitees = [
            recipient[1]
            for recipient in parsed_recipients
            if not search(BOT_REGEX, recipient[1]) and not recipient[1] == sender_email
        ]

        meeting = self.MeetingDetails(
            name=name,
            location=VIRTUAL_RC,
            description=description,
            meeting_start=meeting_start,
            meeting_end=meeting_end,
            length_minutes=int(duration),
            sender_email=sender_email,
            invitees=invitees,
        )

        return meeting

    def create_ics_event(self, meeting: MeetingDetails, cal: Calendar) -> None:
        # Append meeting data to Event object
        event = Event()
        event.name = meeting.name
        event.location = meeting.location
        event.description = meeting.description
        event.begin = meeting.meeting_start
        event.end = meeting.meeting_end
        event.organizer = meeting.sender_email

        # Create attendee list
        for invitee in meeting.invitees:
            event.add_attendee(Attendee(invitee))

        # Add event to "calendar". Calendar is the top level object used to create the .ics file
        cal.events.add(event)

    def send_event_file(
        self, message: Dict[str, Any], bot_handler: BotHandler, cal: Calendar
    ) -> None:
        try:
            with open("my.ics", "w+") as my_file:
                my_file.writelines(cal.serialize_iter())

            # Re-opening file due to issue with empty file when performing operation in the same context-manager
            # TODO figure out how to avoid collisions on the same files when multiple users use this @ alex
            with open("my.ics", "r+") as my_file:
                result = bot_handler.upload_file(my_file)
                response = f"[Meeting Invite]({result['uri']})."
                bot_handler.send_reply(message, response)
                # erase file before close
                my_file.truncate(0)
        except:
            # TODO: find/create better error
            raise FileNotFoundError

    def send_google_event_invite(self, meeting_details: MeetingDetails) -> str:
        try:
            GcalMeeting(meeting_details).send_event()
            return "Google event successfully created!"
        except AuthenticationError:
            return "Google authentication could not be completed. Please reach out to bot owner to reauthenticate."

    def clear_storage(self, bot_handler: BotHandler) -> None:
        bot_handler.storage.put("confirmation", None)
        bot_handler.storage.put("starttime", None)
        bot_handler.storage.put("duration", None)

        return


handler_class = CalendarBotHandler
