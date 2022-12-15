import logging
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

from re import search
from datetime import datetime, timedelta
from tempfile import TemporaryFile

from ics import Attendee, Calendar, Event
from zulip_bots.lib import BotHandler
from zulip_bots.bots.calendarbot.googlecalendar import GcalMeeting as GcalMeeting,authenticate_google, AuthenticationError


logging.basicConfig(filename='zulip_bots/zulip_bots/bots/calendarbot/calendarbot.log', encoding='utf-8', level=logging.DEBUG)


#TODO: Take this from environment variables in the future
BOT_REGEX = "(.*\*\*.*|.*bot.*)"
TIME_FORMAT = "^(<time).*(>)$"
DEFAULT_EVENT_DURATION = 30
VIRTUAL_RC = "https://recurse.rctogether.com/"


class CalendarBotHandler(object):
    """
    This bot fucking loves meetings. 
    """

    @dataclass
    class MeetingDetails:
        sender_email: str
        invitees: list
        meeting_start: datetime
        meeting_end: datetime
        name: str
        summary: str
        length_minutes: int


    def initialize(self, bot_handler: BotHandler) -> None:
        storage = bot_handler.storage

        # Add key values in the bot_handler storage
        if not storage.contains("confirmation"):
            storage.put("confirmation", None)
        if not storage.contains("starttime"):
            storage.put("starttime", None)
        if not storage.contains("duration"):
            storage.put("duration", None)


    def usage(self) -> str:
        return (
            "Calendar Bot creates a calendar meeting for all participants on chat. "
            "Enter a Zulip global time `<time` and then a duration in minutes (e.g. 60 for 1 hour). "
            "Default event duration is 30 mins and default email addresses are from user accounts. "
        )
        

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        storage = bot_handler.storage
        confirmation = storage.get("confirmation")
        starttime = storage.get("starttime")
        duration = storage.get("duration")

         # TODO: Remove after testing
        print(f"Confirmation: {confirmation}\nStart Time: {starttime}'\nDuration: {duration}")

        # TODO: Instantiating Calendar here for now due to bug when trying to move it to init, works but may cause issues in future
        cal = Calendar()

        # Parse the initial message containing the event time and duration info
        if confirmation is None and starttime is None:
            bot_response = self.parse_first_message(message, bot_handler)
            bot_handler.send_reply(message, bot_response)

        # Parse the second message for the meeting info confirmation
        elif confirmation is None and starttime:
            # try:
            #     # Q: Passing in values vs another request to bot_handler
            #     bot_response = self.parse_second_message(message, bot_handler, starttime, duration, cal)
            # except: 
            #     bot_response = f"Could not parse confirmation message: '{message['content']}'. Please message CalendarBot with 'Y' / 'N' to confirm <time:{starttime}>"
            bot_response = self.parse_second_message(message, bot_handler, starttime, cal, duration)

            bot_handler.send_reply(message, bot_response)
        
        #casematch is overkill for now, but i suspect future cases to be added
        # match message_content.split():
        #     case [datetime_input,length_minutes]:         
        #         logging.debug(f"Datetime_input:{datetime_input},length_minutes {length_minutes}")
        #         self.create_and_send_meeting(cal, datetime_input, length_minutes)
        #     case [datetime_input]: 
        #         if datetime_input == 'auth':
        #             authenticate_google()
        #         logging.debug(f"Datetime_input:{datetime_input}")
        #         self.create_and_send_meeting(cal, datetime_input)

        #     case _:
        #         self.input_error_reply()

    
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

        # Validate args Zulip global time and duration
        if not num_args or filtered_args[0] == "help":
            return self.usage()
        elif num_args > 2: 
            return f"Expected at most 2 arguments, received {num_args}"

        if not search(TIME_FORMAT, filtered_args[0]):
            return f"Could not parse '{message['content']}'. Please pass in a Zulip global time `<time`"

        try:
            if num_args == 2:
                duration = int(filtered_args[1])
                bot_handler.storage.put("duration", duration)
        except:
            return f"Could not parse duration input {filtered_args[1]}"

        time = filtered_args[0].replace("<time:", "").replace(">", "")
        bot_handler.storage.put("starttime", time)

        confirm_message = f"Create a meeting at {filtered_args[0]} for {duration} mins? (Y / N)"

        return confirm_message
    
    
    # TODO: Check what occurs when a different sender pings bot
    def parse_second_message(self, message: Dict[str, Any], bot_handler: BotHandler, starttime: str, cal: Calendar, duration: Optional[str] = DEFAULT_EVENT_DURATION) -> None:
        """
        Process confirmation for meeting details in temporary bot_handler storage
        """

        filtered_args = self.message_content_helper(message)
        confirmation = filtered_args[0]

        print(f"Duration2: {duration}")

        if confirmation == "y":
            duration = int(duration)
            meeting_start, meeting_end = self.parse_datetime_input(starttime, duration)
            meeting_details = self.create_meeting_details(meeting_start, meeting_end, message["sender_email"], message["display_recipient"], duration)

            self.create_ics_event(meeting_details, cal)
            self.send_event_file(message, bot_handler, cal)
            self.clear_storage(bot_handler)

            return "Success!"

        elif confirmation == "n":
            self.clear_storage(bot_handler)

            return "Got it! I will remove any saved event data."

        else:
            raise TypeError

    
    def parse_datetime_input(self, starttime: str, duration: int ) -> tuple[datetime, datetime]:
        """
        Converts Zulip global timepicker into a python datetime object
        """

        print(f"Duration3: {duration}")
        meeting_start = datetime.fromisoformat(starttime)
        meeting_end = meeting_start + timedelta(minutes=duration)

        return meeting_start, meeting_end


    def create_meeting_details(self, meeting_start: datetime, meeting_end: datetime, sender_email: str, recipients: List[dict], duration: int) -> MeetingDetails:
        name = "TEST Event Name"
        summary = "TEST Summary"

        # Parse out id and email from recipients
        parsed_recipients = list(map(lambda recipient: (recipient['id'], recipient['email']), recipients))
        # Remove sender and bot from recipient list
        invitees = [recipient[1] for recipient in parsed_recipients if not search(BOT_REGEX, recipient[1]) and not recipient[1] == sender_email]

        # TODO: Remove after debugging
        print(f"Duration4: {duration}")
        print(f"START: {meeting_start}\nEND: {meeting_end}")
        print(f"Parsed Recipients: {parsed_recipients}")
        print(f"Invitees: {invitees}")
        
        meeting = self.MeetingDetails(
                sender_email=sender_email,
                invitees=invitees,
                meeting_start=meeting_start,
                meeting_end=meeting_end,
                length_minutes=int(duration),
                name=name,
                summary=summary)

        return meeting

    
    def create_ics_event(self, meeting: MeetingDetails, cal: Calendar) -> None:    
        # Append meeting data to Event object
        event = Event()
        event.name = meeting.name
        event.location = VIRTUAL_RC
        event.description = meeting.summary
        event.begin = meeting.meeting_start
        event.end =  meeting.meeting_end
        event.organizer = meeting.sender_email
        
        # Create attendee list
        for invitee in meeting.invitees:
            event.add_attendee(Attendee(invitee))

        # Add event to "calendar". Calendar is the top level object used to create the .ics file
        cal.events.add(event)

    
    def send_event_file(self, message: Dict[str, Any], bot_handler: BotHandler, cal: Calendar) -> None:
        try:
            with open('my.ics', 'r+') as my_file:
                my_file.writelines(cal.serialize_iter())

            # Re-opening file due to issue with empty file when performing operation in the same context-manager
            with open('my.ics', 'r+') as my_file:    
                result = bot_handler.upload_file(my_file)
                response = f"[Meeting Invite]({result['uri']})."
                bot_handler.send_reply(message, response)
                #erase file before close
                my_file.truncate(0) 
        except:
            # TODO: find/create better error
            raise FileNotFoundError
    

    def clear_storage(self, bot_handler: BotHandler) -> None:
        bot_handler.storage.put("confirmation", None)
        bot_handler.storage.put("starttime", None)
        bot_handler.storage.put("duration", None)

        return


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    def create_and_send_meeting(self, cal, datetime_input, length_minutes=30):
        try:
            meeting_details = self.parse_meeting_details(datetime_input, length_minutes)
            self.create_calendar_event(meeting_details, cal)
            self.send_google_event_invite(meeting_details)
            self.send_event_file(cal)
        except:
            logging.exception('Error occurred during parsing.')
            self.input_error_reply()


    def send_google_event_invite(self,meeting_details):
        try:
            GcalMeeting(meeting_details).send_event()
        except AuthenticationError: 
            self.authentication_error_reply()
    

    def authentication_error_reply(self):
        response = "Google authentication could not be completed. Please reach out to bot owner to reauthenticate."
        self.bot_handler.send_reply(self.message,response)
        
    def input_error_reply(self):
        logging.error(f"User entered:{self.message['content']} - parsing failed")
        response = "Sorry - I didn't understand that. Please use syntax '[<time:] [duration in minutes, default is 30] '"
        self.bot_handler.send_reply(self.message,response)
          

handler_class = CalendarBotHandler
