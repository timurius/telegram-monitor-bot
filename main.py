import asyncio
from telethon import events, TelegramClient
from json import load, dump

trigger_words = []
chats_to_monitor = []
channel = ''
reply_message = ''

async def save_config(data):
    with open('config.json', 'w') as config_file:
        dump(data, config_file)
        config_file.close()

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
    config_file.close()

session_name = input('Enter the session name (keep the same if you want to keep your account settings): ')
client = TelegramClient(session_name, api_id, api_hash)

@client.on(events.NewMessage(outgoing=True, pattern='!setnotifications'))
async def handler(event):
    channel = event.message.peer_id.channel_id
    await event.message.delete(revoke=True)
    config['notification_channel'] = channel
    await save_config(config)
    print('Set notification channel as: %s'%(channel))

@client.on(events.NewMessage(outgoing=True, pattern='!addchat'))
async def handler(event):
    ch_to_add = event.message.peer_id 
    if hasattr(ch_to_add, 'channel_id'):
        chats_to_monitor.append(ch_to_add.channel_id)
    elif hasattr(ch_to_add, 'chat_id'):
        chats_to_monitor.append(ch_to_add.chat_id)
    else:
        print('You can not add this type of chat to the list!') 
    config['chats'].append(chats_to_monitor[-1])
    await save_config(config)
    print('{} added to chats list. Is channel: {}, is group: {}, is user: {}'.format(chats_to_monitor[-1], hasattr(ch_to_add, 'channel_id'), hasattr(ch_to_add, 'chat_id'), hasattr(ch_to_add, 'user_id')))

@client.on(events.NewMessage(chats=chats_to_monitor))
async def handler(event):
    for trigger_word in trigger_words:
        if trigger_word in event.message.message:
            await client.send_message(event.message.from_id, reply_text)

with client:
    client.run_until_disconnected()

