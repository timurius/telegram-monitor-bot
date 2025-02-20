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

def get_id(peer):
    if hasattr(peer, 'channel_id'):
        return peer.channel_id
    elif hasattr(peer, 'chat_id'):
        return peer.chat_id
    else:
        print('You can not add this type of chat to the list!') 
        return

with open('config.json', 'r') as config_file:
    config = load(config_file)
    config_file.close()

session_name = input('Enter the session name (keep the same if you want to keep your account settings): ')
client = TelegramClient(session_name, config['api_id'], config['api_hash'])

@client.on(events.NewMessage(outgoing=True, pattern='!setnotifications'))
async def handler(event):
    await event.message.delete(revoke=True)
    config['notification_channel'] = event.message.peer_id.channel_id
    await save_config(config)
    print('Set notification channel as: %s'%(channel))

@client.on(events.NewMessage(outgoing=True, pattern='!addchat'))
async def handler(event):
    await event.message.delete(revoke=True)
    ch_id = get_id(event.message.peer_id)
    if ch_id in config['chats']:
        print('The chat is already in the list')
        return
    config['chats'].append(ch_id)
    await save_config(config)
    print('{} added to chats list.'.format(ch_id))

@client.on(events.NewMessage(outgoing=True, pattern='!removechat'))
async def handler(event):
    await event.message.delete(revoke=True)
    ch_id = get_id(event.message.peer_id)
    if ch_id in config['chats']:
        config['chats'].remove(ch_id)
    await save_config(config)

@client.on(events.NewMessage(outgoing=True, pattern='!clearchats'))
async def handler(event):
    await event.message.delete(revoke=True)
    config['chats'].clear()
    await save_config(config)

@client.on(events.NewMessage(chats=chats_to_monitor))
async def handler(event):
    for trigger_word in trigger_words:
        if trigger_word in event.message.message:
            await client.send_message(event.message.from_id, config['reply_message'])

with client:
    client.run_until_disconnected()

