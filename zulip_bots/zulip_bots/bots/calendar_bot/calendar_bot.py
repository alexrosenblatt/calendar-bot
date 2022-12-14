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
DEFAULT_CALEVENT_DURATION = 30
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
    def usage(self) -> str:
        return (
            "Calendar Bot is a meeting scheduler. Enter a Zulip global time `<time` and then a duration in minutes (e.g. 60 for 1 hour). Default event duration is 30 mins and the default email addresses are the emails associated with user emails. There is an option to change invitees with a comma separated list of email addresses."
        )

    def initialize(self, bot_handler: BotHandler) -> None:
        storage = bot_handler.storage

        # Initialize the key values in the bot_handler storage and allows the parsing logic to be a little cleaner
        if not storage.contains("confirmation"):
            storage.put("confirmation", None)
        if not storage.contains("datetime"):
            storage.put("datetime", None)
        if not storage.contains("custom_duration"):
            storage.put("custom_duration", None)
    
    
    def message_content_helper(self, message: Dict[str, Any]) -> List[str]:
        # Split the message string to CalendarBot
        args = message["content"].lower().split()

        # Filter out any arguments that could be related to the bot name. This occurs when there are more than 2 users in the chat.
        return [x for x in args if not re.search(BOT_NAME, x)]

    
    def parse_first_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> str:
        bot_handler.storage.put("Confirmation", None)
        
        filtered_args = self.message_content_helper(message)
        num_args = len(filtered_args)
        duration = DEFAULT_CALEVENT_DURATION

        # Validate args Zulip global time and duration
        if not num_args:
            return self.usage()
        elif num_args > 2: 
            return f"Expected at most 2 arguments, received {num_args}"
        
        if not re.search(TIME_FORMAT, filtered_args[0]):
            return f"Could not parse {message['content']}. Please pass in a Zulip global time `<time`"

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


    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        storage = bot_handler.storage

        # TODO: Remove after testing
        print(bot_handler.storage.get("confirmation"))
        print(bot_handler.storage.get("datetime"))

        # Parse the initial message containing the event time and duration info
        if storage.get("confirmation") is None and storage.get("datetime") is None:
            bot_response = self.parse_first_message(message, bot_handler)
            bot_handler.send_reply(message, bot_response)

        # Parse the second message for the meeting info confirmation
        elif storage.get("confirmation") is None and storage.contains("datetime"):
            try:
                bot_response = self.parse_second_message(message, bot_handler)
            except: 
                bot_response = f"Could not parse confirmation message. Please message CalendarBot with 'Y' / 'N' to confirm <time:{storage.get('datetime')}>"
            
            bot_handler.send_reply(message, bot_response)


handler_class = CalendarHandler
