import re
import os
import sys
import json
import requests
import secrets
import asyncio
import discord
import inspect
import datetime
import pyperclip
import threading
import websockets
import configparser
from uuid import uuid4
from requests import get
from discord.ext import commands
from colorama import init
from discord_webhook import AsyncDiscordWebhook

global check_interval, max_characters, token, channel_id, allow_emojis, allow_links, public, port, logging_enabled, log_type, log_delete_time, message_style, mc_only_synced_accounts, dc_only_synced_accounts, copy_command

def setup():
    global path, date, d_messages, m_messages, running, webhook_request, msg, msg_b, loaded_accounts
    d_messages, m_messages, running, webhook_request, msg = [], [], False, False, ''
    path = os.path.dirname(os.path.abspath(inspect.getframeinfo(inspect.currentframe()).filename))
    date = datetime.datetime.now()
    print(f'{date.day}. {date.month}. {date.year}')
    date = f'{date.year}_{date.month}_{date.day}'
    init()
    print(f'Datei ausgeführt in {path}\\')

    if not os.path.exists(f'{path}/logs'):
        print_color('Erstellt einen Ordner für die Logs', 'yellow')
        os.mkdir(f'{path}/logs')
    
    load_config()
    restore_accounts_file()
    load_accounts()
    if not log_delete_time == -1: clean_logs()

def load_config():
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    try:
        config.read(f'{path}/settings.cfg')
    except configparser.ParsingError:
        if yes_no('Config Datei ist inkorrekt, soll sie zurückgesetzt werden? (Y/n)', 'red'):
            with open(f'{path}/settings.cfg', 'w', encoding='utf-8') as f:
                f.write(requests.get('https://raw.githubusercontent.com/PaperTarsier692/minecraft-bedrock-websocket-python/main/Discord%20Sync/settings.cfg').text.replace('\r\n', '\n'))
        else:
            ask_user_exit()
        config.read(f'{path}/settings.cfg')
    config_settings = config['Highlander Discord Bot Settings']
    for setting in config_settings:
        globals()[setting.lower()] = auto_convert(config_settings[setting])
        if config_settings[setting].replace(' ', '') == '':
            print_color(f'ACHTUNG: {setting} ist nicht im Config angegeben!', 'red')
            ask_user_exit()

def restore_accounts_file():
    if not os.path.exists(f'{path}/synced_accounts.json'):
        print_color('synced_accounts.json wurde gelöscht, lädt die Version von GitHub herunter', 'yellow')
        with open(f'{path}/synced_accounts.json', 'w', encoding='utf-8') as f:
                f.write(requests.get('https://raw.githubusercontent.com/PaperTarsier692/minecraft-bedrock-websocket-python/main/Discord%20Sync/synced_accounts.json').text.replace('\r\n', '\n'))

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

def yes_no(text, color = ''):
    color = color.replace('red', "\033[91m").replace('yellow', "\033[93m").replace('green', "\033[92m").replace('blue', "\033[94m")
    answer = input(color + text + "\033[0m")
    if answer.lower() not in ['y', 'j', 'n']:
        yes_no(text)
    return answer.lower().replace('j', 'y') == 'y'

def print_color(text, color):
    color = color.replace('red', "\033[91m").replace('yellow', "\033[93m").replace('green', "\033[92m").replace('blue', "\033[94m")
    print(color + text + "\033[0m")
    
def ask_user_exit():
    _ = input("\033[91m" + 'Drücke Enter um das Programm zu schließen' + "\033[0m")
    sys.exit()


def clean_logs():
    logs = os.listdir(f'{path}/logs')
    for log in logs:
        if int(log.replace('_', '').replace('.txt', '')) < int(date.replace('_', '')) - log_delete_time:
            print_color(f'Der Log "{log}" wird entfernt', 'yellow')
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
            print_color(f'Timeout nachdem 10 Sekunden lang auf eine Antwort von Minecraft gewarten worden ist.', 'yellow')
            return None
        
async def wait_for_response(uuid):
    global msg
    while True:
        resp_json = msg
        if 'header' in resp_json and 'requestId' in resp_json['header'] and resp_json['header']['requestId'] == str(uuid):
            return resp_json['body']['statusMessage']


async def mineproxy(websocket):
    global websocket_var, webhook_request, loaded_accounts, msg, msg_b, block_pings
    websocket_var = websocket
    
    tasks = [await send(item) for item in d_messages]
    await asyncio.gather(*tasks)
    await websocket.send(json.dumps({"body": {"eventName": "PlayerMessage"},"header": {"requestId": f'{uuid4()}',"messagePurpose": "subscribe","version": 1,"messageType": "commandRequest"}}))
    print_color('Verbunden', 'green')
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
                    print_color(f'Webhook Sync von {user}', 'blue')
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
        copy_string = f'/connect {public_ip}:{port}'
    else:
        ip = 'localhost'
        print('Websocket startet über Private IP')
        copy_string = f'/connect localhost:{port}'
    
    if copy_command and pyperclip.paste() != copy_string: 
        pyperclip.copy(copy_string)
    else:
        print_color(copy_string, 'blue')
    await websockets.serve(mineproxy, ip, port)
    print('Bereit')
    await asyncio.Future()



def discord_bot():
    global loaded_accounts, path
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
        if not channel: 
            print_color('Fehler: Kanal nicht gefunden!', 'red')
            ask_user_exit()
        print(f'Login mit {bot.user}')
        print(f'Belauscht Kanal "{channel}" in Server "{channel.guild.name}"')
    
    @bot.event
    async def on_message(message):
        if message.author == bot.user or message.webhook_id is not None:
            return
        if message.channel == channel and running:
            content = message.content.lower()
            if content == '!account sync':
                if message.author.name not in loaded_accounts['synced_names']:
                    password = secrets.token_hex(8)
                    await message.author.send(f'In Minecraft schreib: !Account sync {password}')
                    accounts = loaded_accounts
                    accounts.get('pending_webhooks').update({f'{message.author.name}': f'{password}'})
                    accounts.get('pending_webhooks_display_names').update({f'{message.author.name}': f'{message.author.display_name}'})
                        
                    with open(f'{path}/synced_accounts.json', 'w') as f:
                        json.dump(accounts, f, indent=4)
                    load_accounts()
                else: print('Ok zu schlecht für uns')
            
            elif content == '!list':
                await message.channel.send(await send('/list', response=True))
     
            elif content == '!kill':
                if message.author.guild_permissions.administrator:
                    print_color(f'Bot durch {message.author} beendet', 'red')
                    asyncio.sleep(3)
                    exit()

            elif await clean_message(message.content, message):
                author = message.author.name
                if author in loaded_accounts['synced_names']:
                    author = loaded_accounts['synced_names'][message.author.name]
                else:
                    author = message.author.display_name
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
                    if not await minecraft_clean_message(message["message"]) == False:
                        await send_webhook(loaded_accounts['synced_webhooks'][message['sender']], await minecraft_clean_message(message["message"]))
                    m_messages.remove(message)
                elif not mc_only_synced_accounts:
                    if not await minecraft_clean_message(message["message"]) == False:
                        await channel.send(f'**<{message["sender"]}>** {await minecraft_clean_message(message["message"])}')
                    m_messages.remove(message)

            if webhook_request != False:
                with open(f'{path}/synced_accounts.json', 'r') as f:
                    accounts = json.load(f)
                guild = channel.guild
                member = discord.utils.get(guild.members, name=webhook_request[0])
                name = accounts['pending_webhooks_display_names'][webhook_request[0]]
                webhook = await channel.create_webhook(name=name, avatar=requests.get(member.avatar.url).content, reason="WebHook für Minecraft/Discord Sync")
                accounts.get('synced_webhooks').update({f'{webhook_request[1]}': f'{webhook.url}'})
                accounts.get('pending_webhooks').pop(member.name, None)
                accounts.get('pending_webhooks_display_names').pop(member.name, None)
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
    
    async def minecraft_clean_message(string):
        if not allow_links:
            string = re.sub(r'http\S+', '', string)
        if max_characters > -1 and len(string) > max_characters:
            return False
        if block_pings != 'disabled':
            if block_pings == 'all':
                string = re.sub(r'<@.*?>', '', string).replace('@everyone', '').replace('@here', '')
        if string.replace(' ', '') == '':
            return False
        else:
            return string


    loop_discord.create_task(d_send_messages())
    try: bot.run(token)
    except discord.errors.LoginFailure: 
        print_color('Fehler: Einloggen bei Discord schiefgelaufen, vielleicht ein inkorrekter Token?', 'red')
        ask_user_exit()
    


def main():
    mc_thread = threading.Thread(target=asyncio.run, args=(init_websocket(),))
    dc_thread = threading.Thread(target=discord_bot)
    mc_thread.start()
    dc_thread.start()
    mc_thread.join()
    dc_thread.join()
    

setup()
main()
