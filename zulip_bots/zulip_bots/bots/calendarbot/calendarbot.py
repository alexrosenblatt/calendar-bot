from icalendar import Calendar, Event, vCalAddress, vText
from zulip_bots.lib import BotHandler
from datetime import date,time,datetime
import logging
import os

logging.basicConfig(filename='calendarbot.log', encoding='utf-8', level=logging.DEBUG)

bot_email = 'test-bot-bot@recurse.zulipchat.com'



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
        meeting_datetime = datetime.fromisoformat(datetime_input.replace('<time:','').replace('>',''))
        sender_id = message['sender_id']

        # get recipients from message json and remove sender and bot
        recipients = list(map(lambda recipient: (recipient['id'],recipient['email']) , message['display_recipient']))
        print(bot_email)
        invitees = [recipient[1] for recipient in recipients if (recipient[0] != sender_id and recipient[1] != bot_email)]
        print(invitees)
        # sender_email = message['email']

        # print(message)
        # bot_handler.send_reply(message,response)

handler_class = CalendarBotHandler
