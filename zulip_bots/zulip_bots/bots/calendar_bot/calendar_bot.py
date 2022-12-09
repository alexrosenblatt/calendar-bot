from typing import Any, Dict, List
import logging
from dataclasses import dataclass, field
from datetime import datetime
import re

from icalendar import Calendar, Event, vCalAddress, vText
from datetime import datetime
from pathlib import Path
import os
import pytz

from zulip_bots.lib import BotHandler

TIME_FORMAT = "^(<time).*(>)$"
BOT_NAME = "(.*\*\*.*|.*bot.*)"
VIRTUAL_RC = "https://recurse.rctogether.com/"


@dataclass
class CalEvent:
    name: str
    sender: str
    recipients: List[str]
    start_time: datetime
    end_time: datetime
    location: str = VIRTUAL_RC


@dataclass
class CalendarHandler:
    event: CalEvent
    cal: Calendar = Calendar()

    def usage(self) -> str:
        return (
            "Calendar Bot is a meeting scheduler. Enter a Zulip global time `<time` and then a duration in minutes (e.g. 60 for 1 hour). Default event duration is 30 mins and the default email addresses are the emails associated with user emails. There is an option to change invitees with a comma separated list of email addresses."
        )


    # def initialize(self, bot_handler: BotHandler) -> None:
    #     storage = bot_handler.storage

    
    def parse_message(self, message_content: str, bot_handler: BotHandler) -> None:
        # Split the message string to CalendarBot
        args = message_content.lower().split()
        # Filter out any arguments that could be related to the bot name. This occurs when there are more than 2 users in the chat.
        filtered_args = [x for x in args if not re.search(BOT_NAME, x)]
        num_args = len(filtered_args)
        
        if num_args > 2: 
            raise TypeError("Expected at most 2 arguments, received {num_args}")

        




    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        content = message["content"]

        if content == "":
            bot_handler.send_reply(message, self.usage())
            return

        # Parse the initial message containing the event time and duration info
        try:
            self.parse_message(content, bot_handler)
        except TypeError as e:
            self.bot_handler.send_reply(message, e)
        except:
            self.bot_handler.send_reply(message, f"Could not parse {content}. Please pass in a Zulip global time `<time`")

    
        bot_handler.send_reply(message, self.message["response"])


handler_class = CalendarHandler




"""
recipient_data = message["display_recipient"]
        # The number of users in the chat group minus the bots
        num_users = len(recipient_data) - 1
        # The user that initiates the bot
        sender_email = message["sender_email"]
        recipient_emails = []

        for r in recipient_data:
            if r["email"] != sender_email and "bot@" not in r["email"]:
                recipient_emails.append(r["email"])


        cal = Calendar()

        # Some RFC5545 SPECIFICATIONS Required items
        cal.add('prodid', '-//My calendar product//example.com//')
        cal.add('version', '2.0')

        # Add subcomponents
        event = Event()
        event.add('name', 'Awesome Meeting')
        event.add('description', 'Description for this awesome meeting')
        event.add('dtstart', datetime(2022, 12, 8, 8, 0, 0, tzinfo=pytz.utc))
        event.add('dtend', datetime(2022, 12, 8, 10, 0, 0, tzinfo=pytz.utc))
        
        # Add the organizer
        organizer = vCalAddress(f"MAILTO:{sender_email}")
        
        # Add parameters of the event
        organizer.params['name'] = vText('John Doe')
        organizer.params['role'] = vText('CEO')
        event['organizer'] = organizer
        event['location'] = vText('New York, USA')
        
        event['uid'] = '2022125T111010/272356262376@example.com'
        event.add('priority', 5)

        for i in recipient_emails:
            attendee = vCalAddress(f"MAILTO:{i}")
            event.add('attendee', attendee, encode=0)
    
            # Add the event to the calendar
            cal.add_component(event)

        directory = str(Path(__file__).parent) + "/"
        print("ics file will be generated at ", directory)
        f = open(os.path.join(directory, 'example.ics'), 'wb')
        f.write(cal.to_ical())
        f.close()

        with open('./zulip_bots/zulip_bots/bots/calendar_bot/example.ics', 'r+') as event:    
            result = bot_handler.upload_file(event)
            response = f"[Calendar Event ICS]({result['uri']})."
            bot_handler.send_reply(message,response)
            event.close()

        return
"""