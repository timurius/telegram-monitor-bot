import asyncio
from telethon import events, TelegramClient
from json import load, dump
from datetime import datetime
from zoneinfo import ZoneInfo

async def save_config(data):
    with open('config.json', 'w', encoding='utf-8') as config_file:
        dump(data, config_file, ensure_ascii=False)
        config_file.close()

def get_id(peer):
    if hasattr(peer, 'channel_id'):
        return peer.channel_id
    elif hasattr(peer, 'chat_id'):
        return peer.chat_id
    else:
        return

async def add_chat(chat_id, config):
    if chat_id in config['chats']:
        print('The chat is already in the list')
        return
    config['chats'].append(chat_id)
    await save_config(config)
    print('{} added to chats list.'.format(chat_id))


def main():
    with open('config.json', 'r', encoding='utf-8') as config_file:
        config = load(config_file)
        config_file.close()
    
    checked_messages = []
    client = TelegramClient('client', config['api_id'], config['api_hash'])
    
    @client.on(events.NewMessage(outgoing=True, pattern='!setnotifications'))
    async def handler(event):
        await event.message.delete(revoke=True)
        try:
            config['notification_channel'] = event.message.peer_id.channel_id
            await save_config(config)
            print('Set notification channel as: %s'%(config['notification_channel']))
        except:
            print('Coldn\'t set notifications channel')
    
    @client.on(events.NewMessage(outgoing=True, pattern='!addchats'))
    async def handler(event):
        await event.message.delete(revoke=True)
        chats_to_add = event.message.message[9:].lower().split(', ')
        for chat_name in chats_to_add:
            try:
                chat = await client.get_input_entity(chat_name)
                chat_id = get_id(chat)
                await add_chat(chat_id, config)
            except:
                print('Couldn\'t add chat: {}'.format(chat_name))

    @client.on(events.NewMessage(outgoing=True, pattern='!addchat$'))
    async def handler(event):
        await event.message.delete(revoke=True)
        try:
            chat_id = get_id(event.message.peer_id)
            await add_chat(chat_id, config)
        except:
            print('Couldn\'t add chat to the list') 

    @client.on(events.NewMessage(outgoing=True, pattern='!removechat'))
    async def handler(event):
        await event.message.delete(revoke=True)
        try:
            ch_id = get_id(event.message.peer_id)
            if ch_id in config['chats']:
                config['chats'].remove(ch_id)
            await save_config(config)
            print('Removed chat: {}'.format(ch_id))
        except:
            print('Couldn\'t remove chat from the list')
    
    @client.on(events.NewMessage(outgoing=True, pattern='!clearchats'))
    async def handler(event):
        await event.message.delete(revoke=True)
        config['chats'].clear()
        await save_config(config)
        print('Cleared chats')
    
    @client.on(events.NewMessage(outgoing=True, pattern='!chats'))
    async def handler(event):
        await event.message.delete(revoke=True)
        ch_list = ''
        if len(config['chats']) == 0:
            await client.send_message(event.peer_id, 'No chats in the list yet')
        else:
            for ch_id in config['chats']:
                try:
                    chat = await client.get_entity(ch_id)
                    ch_list += chat.title + '\n'
                except:
                    ch_list = '__Couldn\'t get chat\'s name (id = {})'.format(ch_id)
            await client.send_message(event.message.peer_id, ch_list)
    
    @client.on(events.NewMessage(outgoing=True, pattern='!addtriggers'))
    async def handler(event):
        await event.message.delete(revoke=True)
        triggers_to_add = event.message.message[13:].lower()
        config['trigger_words'] = list(set(config['trigger_words'] + triggers_to_add.split(', ')))
        await save_config(config)
        print('Added triggers to list: {}'.format(triggers_to_add))
    
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
        print('Removed triggers: {}'.format(triggers_to_remove))
    
    @client.on(events.NewMessage(outgoing=True, pattern='!cleartriggers'))
    async def handler(event):
        await event.message.delete(revoke=True)
        config['trigger_words'].clear()
        await save_config(config)
        print('Cleared triggers')
    
    @client.on(events.NewMessage(incoming=True, chats=config['chats']))
    async def handler(event):
        if any(trigger in event.message.message.lower() for trigger in config['trigger_words']) and config['notification_channel'] != 0 and get_id(event.message.from_id) != config['notification_channel']:
            print(event.message)
            checked_messages.append(event.message.message)
            time = datetime.now().astimezone(ZoneInfo(config["timezone"])).strftime('%d %b %Y, %H:%M')
            try:
                message = event.message.message
            except:
                message = '__Couldn\'t get message content__'
            try:
                from_chat = (await client.get_entity(event.message.peer_id)).title
            except:
                from_chat = '__Couldn\'t get chat name__'
            try:
                message_link = 'https://t.me/c/{}/{}'.format(get_id(event.message.peer_id), event.message.id)
            except:
                message_link = '__Couldn\'t get message link__'
            try:
                from_user = (await client.get_entity(event.message.from_id)).username
            except:
                from_user = '__Couldn\t get username__'
            message_info = '**{}**\n==========================\n**Сообщение**: {}\n==========================\n**Сообщение из**: `{}`\n**Отправитель**: @{}\n**Ссылка на сообщение**: {}'.format(time, message, from_chat, from_user, message_link) 
            await client.send_message(config['notification_channel'], message_info)
        else:
            return
    
    with client:
        print('Bot launched successfully') 
        client.run_until_disconnected()

if __name__ == '__main__':
    main()
