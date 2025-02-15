import asyncio
from telethon import events, TelegramClient

api_id = 0
api_hash = ''
client = TelegramClient('anon', api_id, api_hash)
reply_text = ''

trigger_words = []

@client.on(events.NewMessage())
async def handler(event):
    for trigger_word in trigger_words:
        if trigger_word in event.message.message:
            await client.send_message(event.message.from_id, reply_text)

with client:
    client.run_until_disconnected()

