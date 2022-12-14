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
    # event: CalEvent = field(default_factory=CalEvent())
    # cal: Calendar = field(default_factory=Calendar())

    def usage(self) -> str:
        return (
            "Calendar Bot is a meeting scheduler. Enter a Zulip global time `<time` and then a duration in minutes (e.g. 60 for 1 hour). Default event duration is 30 mins and the default email addresses are the emails associated with user emails. There is an option to change invitees with a comma separated list of email addresses."
        )

    
    def parse_first_response(self, message: Dict[str, Any], bot_handler: BotHandler) -> str:
        bot_handler.storage.put("Confirmation", None)
        # Split the initial message string to CalendarBot
        args = message["content"].lower().split()
        # Filter out any arguments that could be related to the bot name. This occurs when there are more than 2 users in the chat.
        filtered_args = [x for x in args if not re.search(BOT_NAME, x)]
        num_args = len(filtered_args)
        duration = DEFAULT_CALEVENT_DURATION

        # Typechecking for Zulip global time and optional duration argument
        if not num_args:
            return self.usage()
        elif num_args > 2: 
            return f"TypeError: Expected at most 2 arguments, received {num_args}"
        
        if not re.search(TIME_FORMAT, filtered_args[0]):
            return f"Could not parse {message['content']}. Please pass in a Zulip global time `<time`"

        try:
            if num_args == 2:
                duration = int(filtered_args[1])
                bot_handler.storage.put("duration", duration)
        except:
            return f"Could not parse duration input {filtered_args[1]}"

        time = filtered_args[0].replace("<time:", "").replace(">", "")
        bot_handler.storage.put("datetime", time)

        confirm_message = f"Create a meeting at {filtered_args[0]} for {duration}mins? (Y / N)"
        
        return confirm_message
    

    def parse_second_response(message: Dict[str, Any], bot_handler: BotHandler) -> None:
        ... # Y/N in message["content"]
        return 


    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        storage = bot_handler.storage

        print(bot_handler.storage.get("confirmation"))
        print(bot_handler.storage.get("datetime"))

        # Parse the initial message containing the event time and duration info
        if storage.get("confirmation") is None and not storage.contains("datetime"):
            response = self.parse_first_response(message, bot_handler)
            bot_handler.send_reply(message, response)
        elif storage.get("confirmation") is None and storage.contains("datetime"):
            # self.parse_second_response(message, bot_handler)
            ...
        elif storage.get("confirmation") == "Y":
            ... # trigger calevent stuff and then wipe out the storage
        elif storage.get("confirmation") == "N":
            ... # send reply, OK, won't create this! Send self.usage()
            ... # wipe out everything in storage

handler_class = CalendarHandler
