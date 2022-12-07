from ics import Calendar, Event, Attendee
from zulip_bots.lib import BotHandler
from datetime import date,time,datetime,timedelta
import logging
from time import sleep
from tempfile import TemporaryFile
from dataclasses import dataclass
import os

logging.basicConfig(filename='calendarbot.log', encoding='utf-8', level=logging.DEBUG)

#TODO: Take this from environment variables in the future
bot_email = 'test-bot-bot@recurse.zulipchat.com'

#create calendar_object

@dataclass
class MeetingDetails:
    sender_id: int
    invitees: list
    meeting_start: datetime
    meeting_end: datetime
    name: str
    summary: str
    length_minutes: int



class CalendarBotHandler(object):
    """
    This bot fucking loves meetings. 
    """
    def init(self):
        self.message = {}
        self.bot_handler

    def usage(self):
        return """Your description of the bot"""

    def handle_message(self, message:dict, bot_handler):
        self.message = message
        self.bot_handler = bot_handler
        message_content = message['content'].lower()
        cal = Calendar()
        
        #casematch is overkill for now, but i suspect future cases to be added
        match message_content.split():
            case ['meet',datetime_input,length_minutes]:         
                try:
                    length_minutes = int(length_minutes)
                    meeting_details = self.parse_meeting_details(datetime_input)
                    self.create_calendar_event(meeting_details,cal)
                    self.send_event_file(cal)
                except:
                    self.input_error_reply()
            case ['meet',datetime_input]: #TODO add error handling here
                meeting_details = self.parse_meeting_details(datetime_input)
                self.create_calendar_event(meeting_details,cal)
                self.send_event_file(cal)
            case _:
                self.input_error_reply()


    def input_error_reply(self):
        logging.error(f"User entered:{self.message['content']} - parsing failed")
        response = "Sorry - I didn't understand that. Please use syntax 'Meet [<time:] [duration in minutes, default is 30] '"
        self.bot_handler.send_reply(self.message,response)

    def parse_meeting_details(self,datetime_input,length_minutes=30) -> MeetingDetails:
        #converts Zulip global timepicker into a python datetime object
        print(datetime_input)
        meeting_start = datetime.fromisoformat(datetime_input.replace('<time:','').replace('>',''))
        meeting_end = meeting_start+timedelta(minutes=int(length_minutes))
        name = "test name"
        summary = "test summary"
        sender_id = self.message['sender_id']
        

        # get recipients from message json and remove sender and bot
        recipients = list(map(lambda recipient: (recipient['id'],recipient['email']) , self.message['display_recipient']))
        invitees = [recipient[1] for recipient in recipients if (recipient[1] != bot_email)]
        
        meeting = MeetingDetails(sender_id=sender_id,
                invitees=invitees,
                meeting_start=meeting_start,
                meeting_end=meeting_end,
                length_minutes=length_minutes,
                name=name,summary=summary)

        return meeting
    
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
            
            #test attendee
            event.add_attendee(Attendee('sophieduba@gmail.com'))

        # add event to "calendar". Calendar is the top level object used to create the .ics file
        cal.events.add(event)

        # TODO figure out how to make this work
        # with TemporaryFile(mode='r+',prefix='meeting',suffix='.ics') as my_file:
        #     my_file.writelines(cal.serialize_iter())
        #     print(bot_handler.upload_file(my_file))
    

    def send_event_file(self,cal):
        with open('my.ics', 'r+') as my_file:
            my_file.writelines(cal.serialize_iter())
            my_file.close()

        with open('my.ics', 'r+') as my_file:    
            result = self.bot_handler.upload_file(my_file)
            response = f"[Meeting Invite]({result['uri']})."
            self.bot_handler.send_reply(self.message,response)
            
            #erase file before close
            my_file.truncate(0)
            my_file.close()
        
          

handler_class = CalendarBotHandler
