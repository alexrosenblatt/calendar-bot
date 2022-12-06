from ics import Calendar, Event, Attendee
from zulip_bots.lib import BotHandler
from datetime import date,time,datetime,timedelta
import logging
import os

logging.basicConfig(filename='calendarbot.log', encoding='utf-8', level=logging.DEBUG)

#TODO: Take this from environment variables in the future
bot_email = 'test-bot-bot@recurse.zulipchat.com'

#create calendar_object
cal = Calendar()

class CalendarBotHandler(object):
    """
    This bot fucking loves meetings. 
    """


    def usage(self):
        return """Your description of the bot"""

    def handle_message(self, message:dict, bot_handler):
        message_content = message['content'].lower()
        match message_content.split():
            #splits meet command and datetime input
            case ['meet',datetime_input]:
                self.create_calendar_event(self.parse_meeting_details(message,datetime_input))
            case _:
                self.input_error(message,bot_handler)


    def input_error(self,message: dict,bot_handler):
        logging.error(f"User entered:{message['content']} - parsing failed")
        response = "Sorry - I didn't understand that. Please use syntax 'Meet <time'"
        bot_handler.send_reply(message, response)

    def parse_meeting_details(self,message,datetime_input) -> tuple[int,list,datetime,int]:
        #converts Zulip global timepicker into a python datetime object
        meeting_datetime = datetime.fromisoformat(datetime_input.replace('<time:','').replace('>',''))
        sender_id = message['sender_id']
        # sender_email = message['email']
        meeting_length = 30 #TODO make this selectable

        # get recipients from message json and remove sender and bot
        recipients = list(map(lambda recipient: (recipient['id'],recipient['email']) , message['display_recipient']))
        invitees = [recipient[1] for recipient in recipients if (recipient[1] != bot_email)]
        
        return sender_id,invitees,meeting_datetime,meeting_length
    
    def create_calendar_event(self,meeting_details):
        sender_id,invitees,meeting_datetime,meeting_length = meeting_details
        event = Event()
        event.name = "Fun meeting"
        event.begin = meeting_datetime
        event.end = meeting_datetime+timedelta(minutes=meeting_length)
        
        #create attendee list
        map(lambda x: event.add_attendee(x),invitees )

        cal.events.add(event)
        with open('my.ics', 'w') as my_file:
            my_file.writelines(cal.serialize_iter())
        # print(message)
        # bot_handler.send_reply(message,response)
    

handler_class = CalendarBotHandler
