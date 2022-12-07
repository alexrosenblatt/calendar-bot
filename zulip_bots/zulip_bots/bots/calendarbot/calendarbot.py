from ics import Calendar, Event, Attendee
from zulip_bots.lib import BotHandler
from datetime import date,time,datetime,timedelta
import logging
from time import sleep
from tempfile import TemporaryFile
import os

logging.basicConfig(filename='calendarbot.log', encoding='utf-8', level=logging.DEBUG)

#TODO: Take this from environment variables in the future
bot_email = 'test-bot-bot@recurse.zulipchat.com'

#create calendar_object

class CalendarBotHandler(object):
    """
    This bot fucking loves meetings. 
    """

    def usage(self):
        return """Your description of the bot"""

    def handle_message(self, message:dict, bot_handler):
        cal = Calendar()
        message_content = message['content'].lower()
        
        #casematch is overkill for now, but i suspect future cases to be added
        #splits meet command and datetime input
        match message_content.split():
            case ['meet',datetime_input,*ignore]:
                meeting_details = self.parse_meeting_details(message,datetime_input)
                self.create_calendar_event(meeting_details,cal)
                self.send_event_file(bot_handler, cal, message)
            case _:
                self.input_error(message,bot_handler)


    def input_error(self,message: dict,bot_handler):
        logging.error(f"User entered:{message['content']} - parsing failed")
        response = "Sorry - I didn't understand that. Please use syntax 'Meet <time'"
        bot_handler.send_reply(message, response)

    def parse_meeting_details(self,message,datetime_input) -> tuple[int,list,datetime,int,dict]:
        
        #converts Zulip global timepicker into a python datetime object
        meeting_datetime = datetime.fromisoformat(datetime_input.replace('<time:','').replace('>',''))
        sender_id = message['sender_id']
        
        meeting_length = 30 #TODO make this selectable

        # get recipients from message json and remove sender and bot
        recipients = list(map(lambda recipient: (recipient['id'],recipient['email']) , message['display_recipient']))
        invitees = [recipient[1] for recipient in recipients if (recipient[1] != bot_email)]
        
        return sender_id,invitees,meeting_datetime,meeting_length,message
    
    def create_calendar_event(self,meeting_details: tuple[int,list,datetime,int,dict],cal):    
        
        #todo maybe convert the below to named_tuples or a dataclass?
        sender_id,invitees,meeting_datetime,meeting_length,message = meeting_details
        
        #append meeting data to Event object
        event = Event()
        event.name = "Fun meeting"
        event.description = "Wowzers - this meeting is prettttty dope."
        event.begin = meeting_datetime
        event.end = meeting_datetime+timedelta(minutes=meeting_length)
        
        #create attendee list
        for invitee_email in invitees:
            event.add_attendee(Attendee(invitee_email))
            
            #test attendee
            event.add_attendee(Attendee('sophieduba@gmail.com'))

        # add event to "calendar". Calendar is the top level object used to create the .ics file
        cal.events.add(event)

        # TODO figure out how to make this work
        # with TemporaryFile(mode='r+',prefix='meeting',suffix='.ics') as my_file:
        #     my_file.writelines(cal.serialize_iter())
        #     print(bot_handler.upload_file(my_file))
    

    def send_event_file(self, bot_handler, cal, message):
        with open('my.ics', 'r+') as my_file:
            my_file.writelines(cal.serialize_iter())

        #reopening due to some race condition that affect upload files
        with open('my.ics', 'r+') as my_file:    
            result = bot_handler.upload_file(my_file)
            response = f"[Meeting Invite]({result['uri']})."
            bot_handler.send_reply(message,response)
            my_file.close()
          

handler_class = CalendarBotHandler
