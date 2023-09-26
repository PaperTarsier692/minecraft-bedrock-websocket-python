import re
import os
import json
import requests
import secrets
import asyncio
import discord
import inspect
import datetime
import threading
import websockets
import configparser
from discord_webhook import AsyncDiscordWebhook
from uuid import uuid4
from requests import get
from discord.ext import commands

global check_interval, max_characters, token, channel_id, allow_emojis, allow_links, public, port, logging_enabled, log_type, log_delete_time, message_style, mc_only_synced_accounts, dc_only_synced_accounts

def setup():
    global path, date, d_messages, m_messages, running, webhook_request, msg, msg_b, loaded_accounts
    d_messages, m_messages, running, webhook_request, msg = [], [], False, False, ''
    path = os.path.dirname(os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename))
    date = datetime.datetime.now()
    print(f'{date.day}. {date.month}. {date.year}')
    date = f'{date.year}_{date.month}_{date.day}'
    #with open(f'{path}/synced_accounts.json', 'r') as f:
    #    accounts = json.load(f)
    print(f'Datei ausgeführt in {path}\\')

    
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    config.read(f'{path}/settings.cfg')
    config_settings = config['Highlander Discord Bot Settings']
    for setting in config_settings:
        globals()[setting.lower()] = auto_convert(config_settings[setting])
        
    if not log_delete_time == -1: clean_logs()
    load_accounts()
    

def load_accounts():
    global loaded_accounts
    with open(f'{path}/synced_accounts.json', 'r') as f:
        loaded_accounts = json.load(f)
    


def auto_convert(value):
    try: return int(value)
    except ValueError:
        try: return float(value)
        except ValueError:
            if value.lower() in ['true', 'false']: return value.lower() == 'true'
            else: return value

def get_key(val, dict):
   for key, value in dict.items():
      if val == value:
         return key
   return False

def remove_emojis(text):
    regrex_pattern = re.compile(pattern = "["
        u"\U0001F600-\U0001F64F"
        u"\U0001F300-\U0001F5FF"
        u"\U0001F680-\U0001F6FF"
        u"\U0001F1E0-\U0001F1FF"
                           "]+", flags = re.UNICODE)
    return regrex_pattern.sub(r'',text)


def clean_logs():
    logs = os.listdir(f'{path}/logs')
    for log in logs:
        if int(log.replace('_', '').replace('.txt', '')) < int(date.replace('_', '')) - log_delete_time:
            print(f'Der Log "{log}" wird entfernt')
            os.remove(f'{path}/logs/{log}')


def cmd(command:str, arguments=None):
    if msg_b.get('message') != None:
        global match
        if arguments == None:
            match = re.match(command, msg_b.get('message'), re.IGNORECASE)
        elif arguments == 'text':
            match = re.match(f'{command} (\w+)', msg_b.get('message'), re.IGNORECASE)
        elif arguments == 'discord':
            if msg_b.get('type') == 'chat':
                match = {'message' : msg_b.get('message'), 'sender': msg_b.get("sender")}
                return True
            else:
                return False
        return match
    return False

async def send(cmd:str, selector = '@a', response=False):
    uuid = uuid4()
    msg = {"header": {"version": 1,"requestId": f'{uuid}',"messagePurpose": "commandRequest","messageType": "commandRequest"},"body": {"version": 1,"commandLine": cmd,"origin": {"type": "player"}}}
    if cmd.startswith('/') == False:
        if selector == '@sender':
            selector = msg_b.get('sender') 
        msg['body']['commandLine'] = "/tellraw " + selector + '{"rawtext":[{"text":"' + cmd + '"}]}'
    await websocket_var.send(json.dumps(msg))
    if response:
        try:
            return await asyncio.wait_for(wait_for_response(uuid), timeout=True)
        except asyncio.TimeoutError:
            print(f"Timeout nachdem 10 Sekunden auf eine Antwort gewarten worden ist.")
            return None
            
async def wait_for_response(uuid):
    global msg
    while True:
        resp_json = msg
        if 'header' in resp_json and 'requestId' in resp_json['header'] and resp_json['header']['requestId'] == str(uuid):
            return resp_json['body']['statusMessage']

async def mineproxy(websocket):
    global websocket_var, webhook_request, loaded_accounts, msg, msg_b
    websocket_var = websocket
    
    tasks = [await send(item) for item in d_messages]
    await asyncio.gather(*tasks)
    await websocket.send(json.dumps({"body": {"eventName": "PlayerMessage"},"header": {"requestId": f'{uuid4()}',"messagePurpose": "subscribe","version": 1,"messageType": "commandRequest"}}))
    print('Verbunden')
    global running
    running = True
    
    async def send_messages():
        while True:
            for message in d_messages:
                await send(message, '@a[tag=!off]')
                d_messages.remove(message)
            await asyncio.sleep(check_interval)
    asyncio.create_task(send_messages())

    async for msg in websocket:
        msg = json.loads(msg)
        msg_b = msg['body']
        if logging_enabled: 
            with open(f'{path}/logs/{date}.txt', 'a') as f:
                if log_type == 'full':
                    f.write(f'{msg}\n')
                elif log_type == 'short':
                    f.write(f'{msg_b.get("sender")}: {msg_b.get("message")}\n')
        if msg['header'].get('eventName') == 'PlayerMessage':
            if cmd('!Ping'):
                await send(f'§l§8System §r§7: Pong§r', '@sender')
            elif cmd('!Discord', 'text'):
                if match.group(1) == 'disable':
                    await send('/tag @s add off')
                    #await send(f'§l§8System §r§7: Discord Nachrichten sind unsichtbar§r', '@sender')
                elif match.group(1) == 'enable':
                    await send('/tag @s remove off')
                    await send(f'§l§8System §r§7: Discord Nachrichten sind sichtbar§r', '@sender')
            elif cmd('!Account sync', 'text'):
                accounts = loaded_accounts
                user = get_key(match.group(1), accounts['pending_webhooks'])
                if not not user:
                    print(f'Webhook Sync von {user}')
                    with open(f'{path}/synced_accounts.json', 'w') as f:
                        accounts.get('synced_names').update({f'{user}': f'{msg_b.get("sender")}'})
                        global webhook_request
                        webhook_request = ([f'{user}', f'{msg_b.get("sender")}'])
                        json.dump(accounts, f, indent=4)
                    load_accounts()
                    await send(f'§l§8System §r§7: Account erfolgreich synchronisiert!§r', '@sender')
                else: 
                    await send(f'§l§8System §r§7: Falsches Passwort!§r', '@sender')
                    

            elif cmd('', 'discord'):
                m_messages.append(match)
    

async def init_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if public:
        ip = '0.0.0.0'
        public_ip = get('https://api.ipify.org').content.decode('utf8')
        print(f'Websocket startet über Public IP: {public_ip}')
        print(f'/connect {public_ip}:{port}')
    else:
        ip = 'localhost'
        print('Websocket startet über Private IP')
        print(f'/connect localhost:{port}')
    await websockets.serve(mineproxy, ip, port)
    print('Bereit')
    await asyncio.Future()





def discord_bot():
    global loaded_accounts
    loop_discord = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_discord)
    bot = commands.Bot(intents=discord.Intents.all())

    async def error(message, emoji, type):
        if type == 'warn': await message.add_reaction('⚠')
        elif type == 'crit': await message.add_reaction('❌')
        await message.add_reaction(emoji)
    
    @bot.event
    async def on_ready():
        global channel
        channel = bot.get_channel(channel_id)
        if not channel: print('ACHTUNG: Kanal nicht gefunden!')
        print(f'Login mit {bot.user}')
        print(f'Belauscht Kanal {channel} in Server {channel.guild.name}')
    
    @bot.event
    async def on_message(message):
        if message.author == bot.user:
            return
        if message.channel == channel and running:
            if message.content.lower() == '!account sync':
                password = secrets.token_hex(8)
                await message.author.send(f'In Minecraft schreib: !Account sync {password}')
                accounts = loaded_accounts
                accounts.get('pending_webhooks').update({f'{message.author.name}': f'{password}'})
                    
                with open(f'{path}/synced_accounts.json', 'w') as f:
                    json.dump(accounts, f, indent=4)
                load_accounts()

            elif message.content.lower() == '!list':
                await message.channel.send(await send('/list', response=True))
                
            elif message.content.lower() == '!kill':
                exit()

            elif await clean_message(message.content, message):
                author = message.author.display_name
                if message.author in loaded_accounts['synced_names']:
                    author = loaded_accounts['synced_names'][message.author]
                if message_style == 'Highlander':
                    reply = f'§l§9Discord §r§8| §r{author}§7: §r{await clean_message(message.content, message)}'
                elif message_style == 'Default':
                    reply = f'<{author}> {await clean_message(message.content, message)}'
                await send(reply, '@a[tag=!off]')
        
    async def d_send_messages():
        global webhook_request, mc_only_synced_accounts
        while True:
            for message in m_messages:
                if message['sender'] in loaded_accounts['synced_webhooks']:
                    await send_webhook(loaded_accounts['synced_webhooks'][message['sender']], message['message'])
                elif not mc_only_synced_accounts:
                    await channel.send(f'**<{message["sender"]}>** {message["message"]}')
                    m_messages.remove(message)
            if webhook_request != False:
                with open(f'{path}/synced_accounts.json', 'r') as f:
                    accounts = json.load(f)
                guild = channel.guild
                member = discord.utils.get(guild.members, name=webhook_request[0])
                webhook = await channel.create_webhook(name=webhook_request[1], avatar=requests.get(member.avatar.url).content, reason="WebHook für Minecraft/Discord Sync")
                accounts.get('synced_webhooks').update({f'{webhook_request[1]}': f'{webhook.url}'})
                accounts.get('pending_webhooks').pop(member.name, None)
                with open(f'{path}/synced_accounts.json', 'w') as f:
                    json.dump(accounts, f, indent=4)
                webhook_request = False
            await asyncio.sleep(check_interval)

    async def send_webhook(webhook_url, message):
        await AsyncDiscordWebhook(url=webhook_url, content=message).execute()

    async def clean_message(string, message):
        if not allow_emojis:
            if string != remove_emojis(string):
                await error(message, '3️⃣', 'warn')
                string = remove_emojis(string)
        if not allow_links:
            if string != re.sub(r'http\S+', '', string):
                await error(message, '4️⃣', 'warn')
                string = re.sub(r'http\S+', '', string)
        if max_characters > -1 and len(string) > max_characters:
            await error(message, '1️⃣', 'crit')
            return False
        if string.replace(' ', '') == '':
            await error(message, '0️⃣', 'crit')
            return False
        else:
            return string
            


    loop_discord.create_task(d_send_messages())
    bot.run(token)
    


def main():
    mc_thread = threading.Thread(target=asyncio.run, args=(init_websocket(),))
    dc_thread = threading.Thread(target=discord_bot)
    mc_thread.start()
    dc_thread.start()
    mc_thread.join()
    dc_thread.join()
    

setup()
main()
