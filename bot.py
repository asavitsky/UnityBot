from telethon import Button
import asyncio
from telethon import TelegramClient, events
import handlers
import logging
from decouple import config

logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)

api_id = config('api_id')
api_hash = config('api_hash')
bot_token = config('bot_token')
proxy = None
loop = asyncio.new_event_loop()
bot = TelegramClient('bot',  api_id, api_hash, proxy=proxy, loop=loop).start(bot_token=bot_token)


def main():

    bot.add_event_handler(handlers.start)
    bot.add_event_handler(handlers.start_talk)
    bot.add_event_handler(handlers.new_chat)
    bot.add_event_handler(handlers.add_chat)
    bot.add_event_handler(handlers.handler)
    bot.add_event_handler(handlers.edit_chats)
    bot.add_event_handler(handlers.anything_else)
    bot.run_until_disconnected()


if __name__ == '__main__':
    main()
