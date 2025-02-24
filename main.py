import asyncio
from telethon import events, TelegramClient
from json import load, dump

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

@client.on(events.NewMessage(outgoing=True, pattern='!chats'))
async def handler(event):
    await event.message.delete(revoke=True)
    ch_list = ''
    if len(config['chats']) == 0:
        await client.send_message(event.peer_id, 'No chats in the list yet')
    else:
        for ch_id in config['chats']:
            chat = await client.get_entity(ch_id)
            ch_list += chat.title + '\n'
        await client.send_message(event.message.peer_id, ch_list)

#@client.on(events.NewMessage(chats=config['chats']))
#async def handler(event):
#    for trigger_word in config['trigger_words']:
#        if trigger_word in event.message.message:
#            await client.send_message(event.message.from_id, 'hi') 

@client.on(events.NewMessage(outgoing=True, pattern='!addtriggers'))
async def handler(event):
    await event.message.delete(revoke=True)
    triggers_to_add = event.message.message[13:]
    config['trigger_words'] = list(set(config['trigger_words'] + triggers_to_add.split(' ')))
    await save_config(config)

@client.on(events.NewMessage(outgoing=True, pattern='!triggers'))
async def handler(event):
    await event.message.delete(revoke=True)
    await client.send_message(event.message.peer_id, ' '.join(config['trigger_words']))

@client.on(events.NewMessage(outgoing=True, pattern='!removetriggers'))
async def handler(event):
    await event.message.delete(revoke=True)
    triggers_to_remove = event.message.message[len('!removetriggers '):].split(' ')
    config['trigger_words'] = list(set(config['trigger_words']) - set(triggers_to_remove))
    await save_config(config)

with client:
    client.run_until_disconnected()

