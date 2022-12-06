from icalendar import Calendar, Event, vCalAddress, vText
from zulip_bots.lib import BotHandler
from datetime import date,time,datetime
import logging

logging.basicConfig(filename='calendarbot.log', encoding='utf-8', level=logging.DEBUG)



class CalendarBotHandler(object):
    """
    This bot fucking loves meetings. 
    """


    def usage(self):
        return """Your description of the bot"""

    def handle_message(self, message, bot_handler):
        message_content = message['content'].lower()
        match message_content.split():
            #splits meet command and datetime input
            case ['meet',datetime_input]:
                self.new_meeting(message,datetime_input,bot_handler)
            case _:
                self.input_error(message,bot_handler)


    def input_error(self,message,bot_handler):
        logging.error(f"User entered:{message['content']} - parsing failed")
        response = "Sorry - I didn't understand that. Please use syntax 'Meet <time'"
        bot_handler.send_reply(message, response)

    def new_meeting(self,message,datetime_input,bot_handler):
        #converts Zulip global timepicker into a python datetime object
        datetime_parsed = datetime.fromisoformat(datetime_input.replace('<time:','').replace('>',''))
        bot_handler.send_reply(message,datetime_parsed)

handler_class = CalendarBotHandler
