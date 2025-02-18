import asyncio
from telethon import events, TelegramClient
from json import load

with open('config.json', 'r') as config_file:
    config = load(config_file)
    api_id = config['api_id']
    api_hash = config['api_hash']
    if ( len(config['chats']) != 0 ):
        chats_to_monitor = config['chats']
    if ( len(config['trigger_words']) != 0 ):
        trigger_words = config['trigger_words']
    if ( config['notification_channel'] != '' ):
        channel = config['notification_channel'] 
    if ( config['reply_message'] != '' ):
        reply_message = config['reply_message']  

session_name = input('Enter the session name (keep the same if you want to keep your account settings): ')
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage())
async def handler(event):
    for trigger_word in trigger_words:
        if trigger_word in event.message.message:
            await client.send_message(event.message.from_id, reply_text)

with client:
    client.run_until_disconnected()

