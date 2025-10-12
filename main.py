import asyncio
from re import compile as compilere
from re import IGNORECASE as ignr
from telethon import events, TelegramClient
from json import load, dump
from datetime import datetime
from zoneinfo import ZoneInfo
from argparse import ArgumentParser


parser = ArgumentParser(add_help=False)
parser.add_argument('-c', '--config')
parser.add_argument('-s', '--session')
parser.add_arguments('-h', '--cache')
args = parser.parse_args()

if args.config == None:
    config_path = 'config.json'
else:
    config_path = args.config

if args.session == None:
    session_path = 'client'
else:
    session_path = args.session

last_backslash = compilere(r'\/\w').search(session_path)
if last_backslash:
    session_name = session_path[last_backslash.start() + 1:]
else:
    session_name = session_path

if args.cache == None:
    cache_path = session_name + '.json'
else:
    cache_path = args.cache

print('Session name:', session_name)
print('Config file:', config_path)

async def save_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as file:
        dump(data, file, ensure_ascii=False)
        file.close()

def get_id(peer):
    if hasattr(peer, 'channel_id'):
        return peer.channel_id
    elif hasattr(peer, 'chat_id'):
        return peer.chat_id
    elif hasattr(peer, 'user_id'):
        return peer.user_id
    else:
        return

async def add_chat(chat_id, config):
    if chat_id in config['chats']:
        print('Chats is already in the list.')
        return
    config['chats'].append(chat_id)
    await save_file(config_path, config)
    print('{} added to chats list.'.format(chat_id))

async def remove_chat(chat_id, config):
    config['chats'].remove(chat_id)
    await save_file(config_path, config)
    print('{} removed from chats list.'.format(chat_id))

async def ban(user_id, config):
    config['ban_list'].append(user_id)
    await save_file(config_path, config)
    print('{} banned.'.format(user_id))

async def unban(user_id, config):
    config['ban_list'].remove(user_id)
    await save_file(config_path, config)
    print('{} unbanned.'.format(user_id))

def main():
    with open(config_path, 'r', encoding='utf-8') as config_file:
        config = load(config_file)
        config_file.close()

    try:
        cache_file= open(cache_path, 'r', encoding='utf-8')
    except FileNotFoundError:
        cache_file = open(cache_path, 'w', encoding='utf-8')
        cache_file.close()
        cache_file = open(cache_path, 'r', encoding='utf-8')
    finally:
        cache = load(config_file)
        if hasattr(cache, 'reviewed_messages') != True: 
            cache['reviewed_messages'] = set()
        else:
            cache['reviewed_messages_old'] = set(cache['reviewed_messages_old']) 
        if hasattr(cache, 'reviewed_messages_old') != True: 
            cache['reviewed_messages_old'] = set()
        else:
            cache['reviewed_messages'] = set(cache['reviewed_messages']) 
        cache_file.close()

    client = TelegramClient(session_path, config['api_id'], config['api_hash'])
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} setnotifications'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        try:
            config['notification_channel'] = event.message.peer_id.channel_id
            await save_file(config_path, config)
            print('Set notification channel as: {}.'.format(config['notification_channel']))
        except:
            print('Coldn\'t set notifications channel.')
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} addchats'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        ch_to_add = event.message.message[9:].split(', ')
        for ch_name in ch_to_add:
            try:
                chat = await client.get_input_entity(ch_name)
                ch_id = get_id(chat)
                await add_chat(ch_id, config)
            except:
                print('Couldn\'t add chat: {}.'.format(ch_name))

    @client.on(events.NewMessage(outgoing=True, pattern='!{} addchat$'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        try:
            ch_id = get_id(event.message.peer_id)
            await add_chat(ch_id, config)
        except:
            print('Couldn\'t add chat to the list: {}.'.format(e)) 

    @client.on(events.NewMessage(outgoing=True, pattern='!{} removechat$'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        try:
            ch_id = get_id(event.message.peer_id)
            await remove_chat(ch_id, config)
        except:
            print('Couldn\'t remove chat from the list.')

    @client.on(events.NewMessage(outgoing=True, pattern='!{} removechats'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        ch_to_remove = event.message.message[13:].split(', ')
        for ch_name in ch_to_remove:
            try:
                chat = await client.get_input_entity(ch_name)
                ch_id = get_id(chat)
                await remove_chat(ch_id, config)
            except:
                print('Couldn\'t remove chat: {}.'.format(ch_name))
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} clearchats'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        config['chats'].clear()
        await save_file(config_path, config)
        print('Cleared chats.')
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} chats'.format(session_name)))
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
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} addtriggers'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        triggers_to_add = event.message.message[len('!{} addtriggers '.format(session_name)):]
        if triggers_to_add != '':
            config['trigger_words'] = list(set(config['trigger_words'] + triggers_to_add.split(', ')))
            await save_file(config_path, config)
            print('Added triggers to list: {}.'.format(triggers_to_add))
        else:
            print('Can\'t add triggers: no triggers were specified')
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} triggers'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        if len(config['trigger_words']) == 0:
            await client.send_message(event.peer_id, 'No triggers in the list yet')
        else:
            await client.send_message(event.message.peer_id, ', '.join(config['trigger_words']))
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} removetriggers'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        triggers_to_remove = event.message.message[len('!{} removetriggers '.format(session_name)):].split(', ')
        config['trigger_words'] = list(set(config['trigger_words']) - set(triggers_to_remove))
        await save_file(config_path, config)
        print('Removed triggers: {}.'.format(triggers_to_remove))
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} cleartriggers'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        config['trigger_words'].clear()
        await save_file(config_path, config)
        print('Cleared triggers.')

    @client.on(events.NewMessage(outgoing=True, pattern='!{} addnegtriggers'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        triggers_to_add = event.message.message[len('!{} addnegtriggers '.format(session_name)):]
        if triggers_to_add != '':
            config['neg_trigger_words'] = list(set(config['neg_trigger_words'] + triggers_to_add.split(', ')))
            await save_file(config_path, config)
            print('Added negative triggers to list: {}.'.format(triggers_to_add))
        else:
            print('Can\'t add negative triggers: no negative triggers were specified')

    @client.on(events.NewMessage(outgoing=True, pattern='!{} negtriggers'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        if len(config['neg_trigger_words']) == 0:
            await client.send_message(event.peer_id, 'No negative triggers in the list yet')
        else:
            await client.send_message(event.message.peer_id, ', '.join(config['neg_trigger_words']))
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} removenegtriggers'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        triggers_to_remove = event.message.message[len('!{} removenegtriggers '.format(session_name)):].split(', ')
        config['neg_trigger_words'] = list(set(config['neg_trigger_words']) - set(triggers_to_remove))
        await save_file(config_path, config)
        print('Removed negative triggers: {}.'.format(triggers_to_remove))
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} clearnegtriggers'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        config['neg_trigger_words'].clear()
        await save_file(config_path, config)
        print('Cleared negative triggers.')
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} ban( |$)'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        if event.message.is_reply:
            usr_id = get_id(event.message.reply_to.reply_from.from_id) 
            if usr_id != None:
                await ban(usr_id, config)
            else:
                print('Couldn\'t ban user.')
            return
        usr_to_ban = event.message.message[len('!{} ban '.format(session_name)):].split(', ')
        for usr_name in usr_to_ban:
            try:
                usr = await client.get_input_entity(usr_name)
                usr_id = get_id(usr)
                await ban(usr_id, config)
            except:
                print('Couldn\'t ban user: {}.'.format(usr_name))
    
    @client.on(events.NewMessage(outgoing=True, pattern='!{} unban'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        if event.message.is_reply:
            usr_id = get_id(event.message.reply_to.reply_from.from_id) 
            if usr_id != None:
                await unban(usr_id, config)
            return
        usr_to_unban = event.message.message[len('!{} unban '.format(session_name)):].split(', ')
        for usr_name in usr_to_unban:
            try:
                usr = await client.get_input_entity(usr_name)
                usr_id = get_id(usr)
                await unban(usr_id, config)
            except:
                print('Couldn\'t unban user: {}.'.format(usr_name))

    @client.on(events.NewMessage(outgoing=True, pattern='!{} banlist'.format(session_name)))
    async def handler(event):
        await event.message.delete(revoke=True)
        if len(config['ban_list']) == 0:
            await client.send_message(event.peer_id, 'No banned users yet')
        else:
            message = ''
            for usr_id in config['ban_list']:
                usr = await client.get_entity(usr_id)
                if usr.username != None:
                    usr_name = '@' + usr.username
                elif usr.last_name != None:
                    usr_name = usr.first_name + ' ' + usr.last_name 
                else:
                    usr_name = usr.first_name
                message += usr_name + '\n'
            await client.send_message(event.message.peer_id, message)

    @client.on(events.NewMessage(incoming=True))
    async def handler(event):
        from_chat_id = get_id(event.message.peer_id)
        if (config['notification_channel'] != 0) and (get_id(event.message.from_id) != config['notification_channel']) and (from_chat_id in config['chats']) and (get_id(event.message.from_id) not in config['ban_list']):
            for neg_trigger in config['neg_trigger_words']:
                if neg_trigger[:1] == '\\':
                    regex_raw = r'\b{}\b'.format(neg_trigger[1:])
                else:
                    regex_raw = neg_trigger 
                regex = compilere(regex_raw, ignr)

                if regex.search(event.message.message) != None:
                    return

            for trigger in config['trigger_words']:
                if trigger[:1] == '\\':
                    regex_raw = r'\b{}\b'.format(trigger[1:])
                else:
                    regex_raw = trigger
                regex = compilere(regex_raw, ignr)
                if regex.search(event.message.message) != None:
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
                        from_user = '@' + (await client.get_entity(event.message.from_id)).username
                    except:
                        from_user = '__Couldn\'t get username__'
                    message_info = '{}\n==========================\n**{}**\n**Обнаруженное слово**: {}\n**Сообщение из**: `{}`\n**Отправитель**: {}\n**Ссылка на сообщение**: {}'.format(message, time, trigger, from_chat, from_user, message_link) 
                    await client.send_message(config['notification_channel'], message_info)
                    break
                else:
                    continue
        else:
            return
    
    with client:
        print('Bot launched successfully.') 
        client.run_until_disconnected()

if __name__ == '__main__':
    main()
