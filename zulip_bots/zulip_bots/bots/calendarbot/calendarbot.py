import logging
import os
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from tempfile import TemporaryFile
from time import sleep
from re import search

import zulip_bots.bots.calendarbot.googlecalendar as gcal
from ics import Attendee, Calendar, Event
from zulip_bots.lib import BotHandler

logging.basicConfig(filename='calendarbot.log', encoding='utf-8', level=logging.DEBUG)

#TODO: Take this from environment variables in the future
BOT_REGEX = '.+(bot@).+(zulipchat.com)'

#create calendar_object

class CalendarBotHandler(object):
    """
    This bot fucking loves meetings. 
    """
    def init(self):
        self.message = {}
        self.bot_handler
        

    @dataclass
    class MeetingDetails:
        sender_id: int
        invitees: list
        meeting_start: datetime
        meeting_end: datetime
        name: str
        summary: str
        length_minutes: int


    def usage(self):
        return """Creates calendar meeting for all participants on chat."""

    def handle_message(self, message:dict, bot_handler):
        self.message = message
        self.bot_handler = bot_handler
        message_content = message['content'].lower()
        
        #instantiating Calendar() here for now due to bug when trying to move it to init, works but may cause issues in future
        cal = Calendar()

        
        #casematch is overkill for now, but i suspect future cases to be added
        match message_content.split():
            case [datetime_input,length_minutes]:         
                logging.debug(f"Datetime_input:{datetime_input},length_minutes {length_minutes}")
                self.create_and_send_meeting(cal, datetime_input, length_minutes)
            case [datetime_input]: 
                logging.debug(f"Datetime_input:{datetime_input}")
                self.create_and_send_meeting(cal, datetime_input)
            case _:
                self.input_error_reply()

    def create_and_send_meeting(self, cal, datetime_input, length_minutes=30):
        try:
            meeting_details = self.parse_meeting_details(datetime_input,length_minutes)
            self.create_calendar_event(meeting_details,cal)
            self.send_event_file(cal)
        except:
             self.input_error_reply()

    def send_google_event_invite(self,meeting_details):
        gcal.send_google_invite(meeting_details)
        
    def input_error_reply(self):
        logging.error(f"User entered:{self.message['content']} - parsing failed")
        response = "Sorry - I didn't understand that. Please use syntax '[<time:] [duration in minutes, default is 30] '"
        self.bot_handler.send_reply(self.message,response)

    def parse_meeting_details(self,datetime_input,length_minutes) -> MeetingDetails:
        
        #converts Zulip global timepicker into a python datetime object
        meeting_start, meeting_end = self.parse_datetime_input(datetime_input, length_minutes)
        
        name = "test name"
        summary = "test summary"
        sender_id = self.message['sender_id']
        

        # get recipients from message json and remove sender and bot
        recipients = list(map(lambda recipient: (recipient['id'],recipient['email']) , self.message['display_recipient']))
        invitees = [recipient[1] for recipient in recipients if (search(BOT_REGEX,recipient[1]) != True)]
        
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

          

handler_class = CalendarBotHandler
