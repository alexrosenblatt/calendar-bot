import logging
from typing import Any, Dict, List
from dataclasses import dataclass

from re import search
from datetime import datetime, timedelta
from tempfile import TemporaryFile

from ics import Attendee, Calendar, Event
from zulip_bots.lib import BotHandler
from zulip_bots.bots.calendarbot.googlecalendar import GcalMeeting as GcalMeeting,authenticate_google, AuthenticationError


logging.basicConfig(filename='zulip_bots/zulip_bots/bots/calendarbot/calendarbot.log', encoding='utf-8', level=logging.DEBUG)


class CalendarBotHandler(object):
    """
    This bot fucking loves meetings. 
    """

    #TODO: Take this from environment variables in the future
    BOT_REGEX = "(.*\*\*.*|.*bot.*)"
    TIME_FORMAT = "^(<time).*(>)$"
    DEFAULT_CALEVENT_DURATION = 30
    VIRTUAL_RC = "https://recurse.rctogether.com/"


    @dataclass
    class MeetingDetails:
        sender_id: int
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
        if not storage.contains("datetime"):
            storage.put("datetime", None)
        if not storage.contains("custom_duration"):
            storage.put("custom_duration", None)


    def usage(self) -> str:
        return (
            "Calendar Bot creates a calendar meeting for all participants on chat. "
            "Enter a Zulip global time `<time` and then a duration in minutes (e.g. 60 for 1 hour). "
            "Default event duration is 30 mins and default email addresses are from user accounts. "
        )
        

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        storage = bot_handler.storage

         # TODO: Remove after testing
        print(bot_handler.storage.get("confirmation"))
        print(bot_handler.storage.get("datetime"))

        # self.message = message
        # self.bot_handler = bot_handler
        # message_content = message['content'].lower()

        #instantiating Calendar() here for now due to bug when trying to move it to init, works but may cause issues in future
        cal = Calendar()

        # Parse the initial message containing the event time and duration info
        if storage.get("confirmation") is None and storage.get("datetime") is None:
            bot_response = self.parse_first_message(message, bot_handler)
            bot_handler.send_reply(message, bot_response)

        # Parse the second message for the meeting info confirmation
        elif storage.get("confirmation") is None and storage.contains("datetime"):
            try:
                bot_response = self.parse_second_message(message, bot_handler)
            except: 
                bot_response = f"Could not parse confirmation message: '{message['content']}'. Please message CalendarBot with 'Y' / 'N' to confirm <time:{storage.get('datetime')}>"

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
        return [x for x in args if not search(self.BOT_REGEX, x)]


    def parse_first_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> str:
        bot_handler.storage.put("Confirmation", None)

        filtered_args = self.message_content_helper(message)
        num_args = len(filtered_args)
        duration = self.DEFAULT_CALEVENT_DURATION

        # Validate args Zulip global time and duration
        if not num_args or filtered_args[0] == "help":
            return self.usage()
        elif num_args > 2: 
            return f"Expected at most 2 arguments, received {num_args}"

        if not search(self.TIME_FORMAT, filtered_args[0]):
            return f"Could not parse '{message['content']}'. Please pass in a Zulip global time `<time`"

        try:
            if num_args == 2:
                duration = int(filtered_args[1])
                bot_handler.storage.put("custom_duration", duration)
        except:
            return f"Could not parse duration input {filtered_args[1]}"

        time = filtered_args[0].replace("<time:", "").replace(">", "")
        bot_handler.storage.put("datetime", time)

        confirm_message = f"Create a meeting at {filtered_args[0]} for {duration} mins? (Y / N)"

        return confirm_message
    
    
    def parse_second_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        filtered_args = self.message_content_helper(message)
        confirmation = filtered_args[0]

        if confirmation == "y":
            self.create_event(bot_handler)
            return "Success!"
        elif confirmation == "n":
            self.clear_storage(bot_handler)
            return "Got it! I will remove any saved event data."
        else:
            raise TypeError


    def clear_storage(self, bot_handler: BotHandler) -> None:
        bot_handler.storage.put("confirmation", None)
        bot_handler.storage.put("datetime", None)
        bot_handler.storage.put("duration", None)

        return

    def create_event(self, bot_handler: BotHandler) -> None:
        # Remove data from storage
        self.clear_storage(bot_handler)

        return


    #~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~


    def create_and_send_meeting(self, cal, datetime_input, length_minutes=30):
        try:
            meeting_details = self.parse_meeting_details(datetime_input,length_minutes)
            self.create_calendar_event(meeting_details,cal)
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
    

    def parse_meeting_details(self,datetime_input,length_minutes) -> MeetingDetails:
        
        #converts Zulip global timepicker into a python datetime object
        meeting_start, meeting_end = self.parse_datetime_input(datetime_input, length_minutes)
        
        name = "test name"
        summary = "test summary"
        sender_id = self.message['sender_id']
        

        # get recipients from message json and remove sender and bot
        recipients = list(map(lambda recipient: (recipient['id'],recipient['email']) , self.message['display_recipient']))
        invitees = [recipient[1] for recipient in recipients if (search(self.BOT_REGEX,recipient[1]) != True)]
        
        meeting = self.MeetingDetails(sender_id=sender_id,
                invitees=invitees,
                meeting_start=meeting_start,
                meeting_end=meeting_end,
                length_minutes=length_minutes,
                name=name,summary=summary)

        return meeting

    def parse_datetime_input(self, datetime_input, length_minutes) -> tuple[datetime, datetime]:
        meeting_start = datetime.fromisoformat(datetime_input.replace('<time:','').replace('>',''))
        meeting_end = meeting_start+timedelta(minutes=int(length_minutes))
        return meeting_start,meeting_end
    
    def create_calendar_event(self,meeting: MeetingDetails,cal):    
        
        #append meeting data to Event object
   
        event = Event()
        event.name = meeting.name
        event.description = meeting.summary
        event.begin = meeting.meeting_start
        event.end =  meeting.meeting_end
        
        #create attendee list
        for invitee_email in meeting.invitees:
            event.add_attendee(Attendee(invitee_email))

        # add event to "calendar". Calendar is the top level object used to create the .ics file
        cal.events.add(event)
    

    def send_event_file(self,cal):
        try:
            with open('my.ics', 'r+') as my_file:
                my_file.writelines(cal.serialize_iter())

            #Re-opening file due to issue with empty file when performing operation in the same context-manager
            with open('my.ics', 'r+') as my_file:    
                result = self.bot_handler.upload_file(my_file)
                response = f"[Meeting Invite]({result['uri']})."
                self.bot_handler.send_reply(self.message,response)
                #erase file before close
                my_file.truncate(0) 
        except:
            #TODO find/create better error
            raise FileNotFoundError 

    def authentication_error_reply(self):
        response = "Google authentication could not be completed. Please reach out to bot owner to reauthenticate."
        self.bot_handler.send_reply(self.message,response)
        
    def input_error_reply(self):
        logging.error(f"User entered:{self.message['content']} - parsing failed")
        response = "Sorry - I didn't understand that. Please use syntax '[<time:] [duration in minutes, default is 30] '"
        self.bot_handler.send_reply(self.message,response)
          

handler_class = CalendarBotHandler
