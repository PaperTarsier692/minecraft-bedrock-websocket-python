import re  # Filter Emojis, Commands
import os  # Create Directories, Check if Path exists
import sys  # Exit
import json  # JSON Data for sending and recieving WebSocket Data
import random  # Bot Status getting random member
import secrets  # Create a Hex Password for the Sync
import asyncio  # Async Code execution througout the entire project
import discord  # Pycord for the Discord Bot
import inspect  # Get the Path of the currently running Pyhton File
import requests  # Get the Public IP and download Files from GitHub
import datetime  # Get the Date for the logs
import pyperclip  # Copy the command in the Clipboard
import threading  # Pseudo Multithreading
import websockets  # Websockets for Minecraft
import configparser  # Read the Config
from uuid import uuid4  # Generate UUIDs for Minecraft
from requests import get  # The get command for GitHub files
from discord.ext import commands  # Commands for the Discord Bot
from colorama import init  # Coloured Outputs
# WebHooks for the synced Accounts
from discord_webhook import AsyncDiscordWebhook
# Importing my own Misc-Commands
from misc_commands import yes_no, auto_convert, remove_emojis, get_key, print_color

global check_interval, max_characters, token, channel_id, allow_emojis, allow_links, public, port, logging_enabled, log_type, log_delete_time, message_style, mc_only_synced_accounts, dc_only_synced_accounts, copy_command, language

global gn_date_format, gn_file_executed_in, gn_folder_created_for_logs, gn_log_deleted, gn_config_file_broken, gn_setting_empty, gn_restore_synced_accounts, gn_ask_user_for_exit, mc_ws_timeout, mc_ws_public_ip, mc_ws_private_ip, mc_ws_ready, mc_ws_connected, mc_new_wh_sync, mc_succesful_sync, mc_wrong_password, mc_dc_messages_hidden, dc_login, dc_channel_server_message, dc_channel_not_found, dc_login_error, dc_wh_dm_msg, dc_bot_killed, dc_wh_reason, mc_dc_messages_visible
# This ist just temporary and could be removed (but your IDE is gonna throw a lot of variable undefined errors)


def setup():
    global path, date, d_messages, m_messages, running, webhook_request, msg, msg_b, loaded_accounts
    d_messages, m_messages, running, webhook_request, msg = [], [], False, False, ''
    path = os.path.dirname(os.path.abspath(
        inspect.getframeinfo(inspect.currentframe()).filename))
    date_obj = datetime.datetime.now()
    date = f'{date_obj.year}_{date_obj.month}_{date_obj.day}'
    init()

    if not os.path.exists(f'{path}/logs'):
        print_color(gn_folder_created_for_logs)
        os.mkdir(f'{path}/logs')
    global setting_empty
    gn_setting_empty = '//red// ERROR: % ist nicht im Config angegeben!'
    load_config()
    load_lang()
    restore_accounts_file()
    load_accounts()
    if not log_delete_time == -1:
        clean_logs()
    print_color(gn_file_executed_in.replace('%', path))
    print_color(f'{date_obj.day}. {date_obj.month}. {date_obj.year}')


def ask_user_exit():
    print_color(gn_ask_user_for_exit)
    _ = input()
    sys.exit()


def load_config():
    config = configparser.ConfigParser()
    config.optionxform = lambda option: option
    try:
        config.read(f'{path}/settings.cfg')
    except configparser.ParsingError:
        if yes_no(gn_config_file_broken):
            with open(f'{path}/settings.cfg', 'w', encoding='utf-8') as f:
                f.write(requests.get(
                    'https://raw.githubusercontent.com/PaperTarsier692/minecraft-bedrock-websocket-python/main/Discord%20Sync/settings.cfg').text.replace('\r\n', '\n'))
        else:
            ask_user_exit()
        config.read(f'{path}/settings.cfg')
    config_settings = config['Highlander Discord Bot Settings']
    for setting in config_settings:
        globals()[setting.lower()] = auto_convert(config_settings[setting])
        if config_settings[setting].replace(' ', '') == '':
            print_color(setting_empty.replace('%', setting))
            ask_user_exit()


def restore_accounts_file():
    if not os.path.exists(f'{path}/synced_accounts.json'):
        print_color(gn_restore_synced_accounts)
        with open(f'{path}/synced_accounts.json', 'w', encoding='utf-8') as f:
            f.write(requests.get(
                'https://raw.githubusercontent.com/PaperTarsier692/minecraft-bedrock-websocket-python/main/Discord%20Sync/synced_accounts.json').text.replace('\r\n', '\n'))


def load_accounts():
    global loaded_accounts
    with open(f'{path}/synced_accounts.json', 'r') as f:
        loaded_accounts = json.load(f)


def load_lang():
    global lang_file, language
    with open(f'{path}/lang/{language}.lang', 'r', encoding='utf-8') as l:
        lang_file = l.read()
    split = lang_file.splitlines()
    for element in split:
        if not element.startswith('#'):
            globals()[element.split('=', 1)[0]] = element.split('=')[1].replace('\\n', '\n')


def clean_logs():
    logs = os.listdir(f'{path}/logs')
    for log in logs:
        if int(log.replace('_', '').replace('.txt', '')) < int(date.replace('_', '')) - log_delete_time:
            print_color(gn_log_deleted.replace('%', log))
            os.remove(f'{path}/logs/{log}')


def cmd(command: str, arguments=None):
    if msg_b.get('message') != None:
        global match
        if arguments == None:
            match = re.match(command, msg_b.get('message'), re.IGNORECASE)
        elif arguments == 'text':
            match = re.match(f'{command} (\w+)',
                             msg_b.get('message'), re.IGNORECASE)
        elif arguments == 'discord':
            if msg_b.get('type') == 'chat':
                match = {'message': msg_b.get(
                    'message'), 'sender': msg_b.get("sender")}
                return True
            else:
                return False
        return match
    return False


async def send(cmd: str, selector='@a', response=False):
    uuid = uuid4()
    msg = {"header": {"version": 1, "requestId": f'{uuid}', "messagePurpose": "commandRequest",
                      "messageType": "commandRequest"}, "body": {"version": 1, "commandLine": cmd, "origin": {"type": "player"}}}
    if cmd.startswith('/') == False:
        if selector == '@sender':
            selector = msg_b.get('sender')
        msg['body']['commandLine'] = "/tellraw " + \
            selector + '{"rawtext":[{"text":"' + cmd + '"}]}'
    await websocket_var.send(json.dumps(msg))
    if response:
        try:
            return await asyncio.wait_for(wait_for_response(uuid), timeout=True)
        except asyncio.TimeoutError:
            print_color(mc_ws_timeout)
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
    await websocket.send(json.dumps({"body": {"eventName": "PlayerMessage"}, "header": {"requestId": f'{uuid4()}', "messagePurpose": "subscribe", "version": 1, "messageType": "commandRequest"}}))
    print_color(mc_ws_connected)
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
                    await send(f'§l§8System §r§7: {mc_dc_messages_hidden}§r', '@sender')
                elif match.group(1) == 'enable':
                    await send('/tag @s remove off')
                    await send(f'§l§8System §r§7: Discord {mc_dc_messages_visible}§r', '@sender')
            elif cmd('!Account sync', 'text'):
                user = get_key(match.group(
                    1), loaded_accounts['pending_webhooks'])
                if not not user:
                    print_color(mc_new_wh_sync.replace('%', user))
                    with open(f'{path}/synced_accounts.json', 'w') as f:
                        loaded_accounts.get('synced_names').update(
                            {f'{user}': f'{msg_b.get("sender")}'})
                        global webhook_request
                        webhook_request = (
                            [f'{user}', f'{msg_b.get("sender")}'])
                        json.dump(loaded_accounts, f, indent=4)
                    load_accounts()
                    await send(f'§l§8System §r§7: {mc_succesful_sync}§r', '@sender')
                else:
                    await send(f'§l§8System §r§7: {mc_wrong_password}§r', '@sender')

            elif cmd('', 'discord'):
                m_messages.append(match)


async def init_websocket():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    if public:
        ip = '0.0.0.0'
        public_ip = get('https://api.ipify.org').content.decode('utf8')
        print_color(mc_ws_public_ip.replace('%', public_ip))
        copy_string = f'/connect {public_ip}:{port}'
    else:
        ip = 'localhost'
        print_color(mc_ws_private_ip)
        copy_string = f'/connect localhost:{port}'

    if copy_command and pyperclip.paste() != copy_string:
        pyperclip.copy(copy_string)
    else:
        print_color(copy_string)
    await websockets.serve(mineproxy, ip, port)
    print_color(mc_ws_ready)
    await asyncio.Future()


def discord_bot():
    global loaded_accounts, path
    loop_discord = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_discord)
    bot = commands.Bot(intents=discord.Intents.all())

    async def error(message, emoji, type):
        if type == 'warn':
            await message.add_reaction('⚠')
        elif type == 'crit':
            await message.add_reaction('❌')
        await message.add_reaction(emoji)

    @bot.event
    async def on_ready():
        global channel
        channel = bot.get_channel(channel_id)
        if not channel:
            print_color(dc_channel_not_found)
            ask_user_exit()
        print_color(dc_login.replace('%', str(bot.user)))
        print_color(dc_channel_server_message.replace(
            '%1', str(channel)).replace('%2', str(channel.guild.name)))
        loop_discord.create_task(status())

    @bot.event
    async def on_message(message):
        if message.author == bot.user or message.webhook_id is not None:
            return
        if message.channel == channel and running:
            content = message.content.lower()
            if content == '!account sync':
                if message.author.name not in loaded_accounts['synced_names']:
                    password = secrets.token_hex(8)
                    await message.author.send(dc_wh_dm_msg.replace('%', f'!Account sync {password}'))
                    loaded_accounts.get('pending_webhooks').update(
                        {f'{message.author.name}': f'{password}'})
                    loaded_accounts.get('pending_webhooks_display_names').update(
                        {f'{message.author.name}': f'{message.author.display_name}'})

                    with open(f'{path}/synced_accounts.json', 'w') as f:
                        json.dump(loaded_accounts, f, indent=4)
                    load_accounts()
                else:
                    pass

            elif content == '!list':
                await message.channel.send(await send('/list', response=True))

            elif content == '!kill':
                if message.author.guild_permissions.administrator:
                    print_color(dc_bot_killed.replace(
                        '%', message.author.name))
                    await asyncio.sleep(3)
                    exit()

            elif await clean_message(message.content, message):
                author = message.author.name
                if author in loaded_accounts['synced_names']:
                    author = loaded_accounts['synced_names'][message.author.name]
                else:
                    if dc_only_synced_accounts:
                        return
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
                member = discord.utils.get(
                    guild.members, name=webhook_request[0])
                name = accounts['pending_webhooks_display_names'][webhook_request[0]]
                webhook = await channel.create_webhook(name=name, avatar=requests.get(member.avatar.url).content, reason=dc_wh_reason)
                accounts.get('synced_webhooks').update(
                    {f'{webhook_request[1]}': f'{webhook.url}'})
                accounts.get('pending_webhooks').pop(member.name, None)
                accounts.get('pending_webhooks_display_names').pop(
                    member.name, None)
                with open(f'{path}/synced_accounts.json', 'w') as f:
                    json.dump(accounts, f, indent=4)
                webhook_request = False
            await asyncio.sleep(check_interval)

    async def status():
        counter = 0
        while not running:
            await asyncio.sleep(1)
        while True:
            counter += 1
            counter %= 5

            if counter == 1:
                await bot.change_presence(activity=discord.Game(name="Minecraft Highlander"))
            elif counter == 2:
                members = await send('/list', response=True)
                members = members.split(':')[1].splitlines()
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=members[random.randint(0, len(members) - 1)]))
            elif counter == 3:
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="https://discord.gg/KwgtbJFpk4"))
            elif counter == 4:
                members = await send('/list', response=True)
                members = members.split(':')[0]
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=members))

            elif counter == 5:
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Swims Schreie"))
            await asyncio.sleep(15)

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
                string = re.sub(
                    r'<@.*?>', '', string).replace('@everyone', '').replace('@here', '')
        if string.replace(' ', '') == '':
            return False
        else:
            return string

    loop_discord.create_task(d_send_messages())

    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        print_color(dc_login_error)
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
