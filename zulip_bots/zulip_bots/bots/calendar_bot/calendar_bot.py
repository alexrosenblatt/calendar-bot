from typing import Any, Dict

from zulip_bots.lib import BotHandler


class CalendarHandler:
    def usage(self) -> str:
        return """
        This is a boilerplate bot.
        """

    def handle_message(self, message: Dict[str, Any], bot_handler: BotHandler) -> None:
        # content = message["content"]

        bot_handler.send_reply(message, message)
        return


handler_class = CalendarHandler

    