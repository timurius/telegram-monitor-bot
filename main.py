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

checked_messages = []
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

@client.on(events.NewMessage(outgoing=True, pattern='!addtriggers'))
async def handler(event):
    await event.message.delete(revoke=True)
    triggers_to_add = event.message.message[13:].lower()
    config['trigger_words'] = list(set(config['trigger_words'] + triggers_to_add.split(', ')))
    await save_config(config)

@client.on(events.NewMessage(outgoing=True, pattern='!triggers'))
async def handler(event):
    await event.message.delete(revoke=True)
    if len(config['trigger_words']) == 0:
        await client.send_message(event.peer_id, 'No triggers in the list yet')
    else:
        await client.send_message(event.message.peer_id, ', '.join(config['trigger_words']))

@client.on(events.NewMessage(outgoing=True, pattern='!removetriggers'))
async def handler(event):
    await event.message.delete(revoke=True)
    triggers_to_remove = event.message.message[len('!removetriggers '):].split(' ')
    config['trigger_words'] = list(set(config['trigger_words']) - set(triggers_to_remove))
    await save_config(config)

@client.on(events.NewMessage(outgoing=True, pattern='!cleartriggers'))
async def handler(event):
    await event.message.delete(revoke=True)
    config['trigger_words'].clear()
    await save_config(config)

@client.on(events.NewMessage(incoming=True, chats=config['chats']))
async def handler(event):
    if event.message.message in checked_messages: #for whatever reason if this check is not done bot will forward messages infinitly, so better keep it
        checked_messages.remove(event.message.message) 
        return
    else:
        if any(trigger in event.message.message.lower() for trigger in config['trigger_words']):
            checked_messages.append(event.message.message)
            from_chat = await client.get_entity(event.message.peer_id)
            message_link = 'https://t.me/c/{}/{}'.format(get_id(event.message.peer_id), event.message.id)
            message_info = '**Сообщение из**: `{}`\n**Ссылка на сообщение**: {}'.format(from_chat.title, message_link) 
            await event.message.forward_to(config['notification_channel'])
            await client.send_message(config['notification_channel'], message_info)
        else:
            return

with client:
    client.run_until_disconnected()
