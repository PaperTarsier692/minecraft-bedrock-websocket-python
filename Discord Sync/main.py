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
from discord_webhook import AsyncDiscordWebhook
# WebHooks for the synced Accounts
from misc_commands import *
# Importing my own Misc-Commands

global check_interval, max_characters, token, channel_id, allow_emojis, allow_links, public, port, logging_enabled, log_type, log_delete_time, message_style, mc_only_synced_accounts, dc_only_synced_accounts, copy_command, language, enable_webhooks

global gn_date_format, gn_file_executed_in, gn_folder_created_for_logs, gn_log_deleted, gn_config_file_broken, gn_setting_empty, gn_restore_synced_accounts, gn_ask_user_for_exit, mc_ws_timeout, mc_ws_public_ip, mc_ws_private_ip, mc_ws_ready, mc_ws_connected, mc_new_wh_sync, mc_succesful_sync, mc_wrong_password, mc_dc_messages_hidden, dc_login, dc_channel_server_message, dc_channel_not_found, dc_login_error, dc_account_sync_request, dc_bot_killed, dc_wh_reason, mc_dc_messages_visible, mc_wh_creation_failed, mc_succesful_desync, dc_account_already_synced
# This ist just temporary and could be removed (but your IDE is gonna throw a lot of variable undefined errors)


def setup():
    '''Loads the files, and does some other small things'''
    global path, date, d_messages, m_messages, running, webhook_request, msg, msg_b, loaded_accounts
    d_messages, m_messages, running, webhook_request, msg = [], [], False, False, ''
    global gn_setting_empty, gn_folder_created_for_logs
    gn_setting_empty, gn_folder_created_for_logs = '//red// ERROR: % ist nicht im Config angegeben!', '//yellow// Erstellt einen Ordner für die Logs'
    path = os.path.dirname(os.path.abspath(
        inspect.getframeinfo(inspect.currentframe()).filename))
    date_obj = datetime.datetime.now()
    date = f'{date_obj.year}_{date_obj.month}_{date_obj.day}'
    init()

    if not os.path.exists(f'{path}/logs'):
        print_color(gn_folder_created_for_logs)
        os.mkdir(f'{path}/logs')

    load_config()
    load_lang()
    restore_accounts_file()
    load_accounts()
    if not log_delete_time == -1:
        clean_logs()
    print_color(gn_file_executed_in.replace('%', path))
    print_color(f'{date_obj.day}. {date_obj.month}. {date_obj.year}')


def ask_user_exit():
    '''Asks the user if he wants to exit the programm'''
    print_color(gn_ask_user_for_exit)
    _ = input()
    sys.exit()


def load_config():
    '''Loads the config and saves the settings in global variables'''
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
            print_color(gn_setting_empty.replace('%', setting))
            ask_user_exit()


def restore_accounts_file():
    '''Checks if the synced_accounts file still exists, and if it doesn't downloads a new copy from GitHub'''
    if not os.path.exists(f'{path}/synced_accounts.json'):
        print_color(gn_restore_synced_accounts)
        with open(f'{path}/synced_accounts.json', 'w', encoding='utf-8') as f:
            f.write(requests.get(
                'https://raw.githubusercontent.com/PaperTarsier692/minecraft-bedrock-websocket-python/main/Discord%20Sync/synced_accounts.json').text.replace('\r\n', '\n'))


def load_accounts():
    '''Loads the synced_accounts.json file and stores it in the global 'loaded_accounts' variable'''
    global loaded_accounts
    with open(f'{path}/synced_accounts.json', 'r') as f:
        loaded_accounts = json.load(f)
        
def save_accounts():
    '''Saves the 'loaded_accounts' in the 'synced_accounts.json' file'''
    with open(f'{path}/synced_accounts.json', 'w') as f:
        json.dump(loaded_accounts, f, indent=4)


def load_lang():
    '''Loads the .lang file given in the settings and loads every phrase in a seperate global variable'''
    global lang_file, language
    with open(f'{path}/lang/{language}.lang', 'r', encoding='utf-8') as l:
        lang_file = l.read()
    split = lang_file.splitlines()
    for element in split:
        if not element.startswith('#'):
            globals()[element.split('=', 1)[0]] = element.split('=')[1].replace('\\n', '\n')


def clean_logs():
    '''Cleans out old logs, that are more days old, than the value specified in the settings'''
    logs = os.listdir(f'{path}/logs')
    for log in logs:
        if int(log.replace('_', '').replace('.txt', '')) < int(date.replace('_', '')) - log_delete_time:
            print_color(gn_log_deleted.replace('%', log))
            os.remove(f'{path}/logs/{log}')


def cmd(command: str, arguments=None):
    '''A function for checking if a certain command was called in Minecraft\n
    Examples:\r
    if cmd('!ping'): => True if the command was sent in chat (commands need to be lowercase)\n
    if cmd('!say', 'text'):\n
        await send(match.group(1)) => Allows for text to be sent after the '!say' command, which is stored in 'match.group(1)\n'
    if cmd('', 'discord'): => Always is true, as long as the message comes from a player'''
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
    '''Send something in the MC chat using WebSockets
    Examples:
    await send('Hello World') => Sends 'Hello World' into the chat (with tellraw)
    await send('/list', response=True) -> 'There are 1/8 players online: ...'
    await send('Hello Paper', selector='@PaperTarsier692') -> Sends 'Hello Paper' to @PaperTarsier692
    await send('Pong', selector='@sender') -> Sends the message to the user who sent the command (Only works when executing it on a command)
    '''
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
            return await asyncio.wait_for(_wait_for_response(uuid), timeout=True)
        except asyncio.TimeoutError:
            print_color(mc_ws_timeout)
            return None


async def _wait_for_response(uuid):
    global msg
    while True:
        resp_json = msg
        if 'header' in resp_json and 'requestId' in resp_json['header'] and resp_json['header']['requestId'] == str(uuid):
            return resp_json['body']['statusMessage']


async def mineproxy(websocket):
    '''The function running the WebSocket'''
    global websocket_var, webhook_request, loaded_accounts, msg, msg_b, block_pings
    websocket_var = websocket

    tasks = [await send(item) for item in d_messages]
    await asyncio.gather(*tasks)
    await websocket.send(json.dumps({"body": {"eventName": "PlayerMessage"}, "header": {"requestId": f'{uuid4()}', "messagePurpose": "subscribe", "version": 1, "messageType": "commandRequest"}}))
    print_color(mc_ws_connected)
    global running
    running = True

    async for msg in websocket:
        msg = json.loads(msg)
        msg_b = msg['body']
        if log_type != 'off':
            with open(f'{path}/logs/{date}.txt', 'a') as f:
                if log_type == 'full':
                    f.write(f'{msg}\n')
                elif log_type == 'short':
                    f.write(f'{msg_b.get("sender")}: {msg_b.get("message")}\n')

        if msg['header'].get('eventName') == 'PlayerMessage':
            if cmd('!Discord', 'text'):
                if match.group(1) == 'disable':
                    await send('/tag @s add off')
                    await send(f'§l§8System §r§7: {mc_dc_messages_hidden}§r', '@sender')
                elif match.group(1) == 'enable':
                    await send('/tag @s remove off')
                    await send(f'§l§8System §r§7: Discord {mc_dc_messages_visible}§r', '@sender')

            elif cmd('!Account', 'text'):
                if cmd('!Account sync', 'text'):
                    #---Try to get the user infos---
                    password = match.group(1)
                    user = loaded_accounts['pending_webhooks'].get(password)
                    
                    if user != None:
                        #---Add the Minecraft Name to the users info and start a WebHook request---
                        print_color(mc_new_wh_sync.replace('%', msg_b.get('sender')))
                        webhook_request = password
                        loaded_accounts['pending_webhooks'].get(password)['minecraft_name'] = msg_b.get('sender')
                        await send(f'§l§8System §r§7: {mc_succesful_sync}§r', '@sender')
                    else:
                        #If the user/password isn't found, throw an error
                        await send(f'§l§8System §r§7: {mc_wrong_password}§r', '@sender')
                
                elif cmd('!Account desync'):
                    user = msg_b.get('sender')
                    if user in loaded_accounts['synced_webhooks']:
                        loaded_accounts['synced_webhooks'].pop(user)
                        loaded_accounts['synced_names'].pop(get_key(user, loaded_accounts['synced_names']))
                        save_accounts()
                        await send(f'§l§8System §r§7: {mc_succesful_desync}§r', '@sender')

            elif cmd('', 'discord'):
                m_messages.append(match)


async def init_websocket():
    '''Initialises the WebSocket and runs some misc things, like copying the command in the clipboard'''
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    #Setup

    #---Run on private/public IP---
    if public:
        #If the public IP address gets selected, get it with the ipify API and print it
        ip = '0.0.0.0'
        public_ip = get('https://api.ipify.org').content.decode('utf8')
        print_color(mc_ws_public_ip.replace('%', public_ip))
        copy_string = f'/connect {public_ip}:{port}'
    else:
        #If the private IP address gets selected, use the localhost as IP
        ip = 'localhost'
        print_color(mc_ws_private_ip)
        copy_string = f'/connect localhost:{port}'

    #---Copy or output the command---
    if copy_command and pyperclip.paste() != copy_string:
        #Only copy the command if enabled in the settings, and the command isn't already in the clipboard
        pyperclip.copy(copy_string)
    else:
        #Else print the command to the console
        print_color(copy_string)
    
    #---Start the WebSocket listener---
    await websockets.serve(mineproxy, ip, port)
    print_color(mc_ws_ready)
    await asyncio.Future()


def discord_bot():
    '''The function running the Discord Bot'''
    global loaded_accounts, path
    loop_discord = asyncio.new_event_loop()
    asyncio.set_event_loop(loop_discord)
    bot = commands.Bot(intents=discord.Intents.all())
    #Setup

    async def error(message, emoji, type):
        if type == 'warn':
            await message.add_reaction('⚠')
        elif type == 'crit':
            await message.add_reaction('❌')
        await message.add_reaction(emoji)

    @bot.event
    async def on_ready():
        '''The function that gets called as soon as the bot gets connected'''
        global channel
        channel = bot.get_channel(channel_id)
        if not channel:
            #Execute if the channel is not found
            print_color(dc_channel_not_found)
            ask_user_exit()
        print_color(dc_login.replace('%', str(bot.user)))
        print_color(dc_channel_server_message.replace(
            '%1', str(channel)).replace('%2', str(channel.guild.name)))
        loop_discord.create_task(status())
        #Start the status() loop in the background

    @bot.event
    async def on_message(message):
        '''The function that gets called every recieved message'''
        if message.author == bot.user or message.webhook_id is not None:
            #Don't do further checks if the user is from this bot or a WebHook
            return
        if message.channel == channel and running:
            content = message.content.lower()
            if content == '!account sync':
                if message.author.name not in loaded_accounts['synced_names']:
                    #---Create a password and send it to the user---
                    password = secrets.token_hex(8)
                    await message.author.send(dc_account_sync_request.replace('%', f'!Account sync {password}'))
                    #---Gather the users info and save it---
                    user_infos = {
                        'discord_tag': message.author.name,
                        'discord_name': message.author.display_name,
                        'minecraft_name': 'placeholder'
                    }
                    loaded_accounts.get('pending_webhooks').update(
                        {password: user_infos})
                    #---Save the changes to the synced_accounts.json file---
                    save_accounts()

                else:
                    await message.author.send(dc_account_already_synced)

            elif content == '!list':
                await message.channel.send(await send('/list', response=True))
                #Respond with the result of the /list command

            elif content == '!kill':
                if message.author.guild_permissions.administrator:
                    #Only execute if the user has Admin permissions
                    print_color(dc_bot_killed.replace(
                        '%', message.author.name))
                    sys.exit()
                    #Wait 3 seconds before closing the programm

            elif await clean_message(message):
                author = message.author.name
                if author in loaded_accounts['synced_names']:
                    author = loaded_accounts['synced_names'][author]
                else:
                    if dc_only_synced_accounts:
                        return
                    author = message.author.display_name
                if message_style == 'Highlander':
                    reply = f'§l§9Discord §r§8| §r{author}§7: §r{await clean_message(message)}'
                elif message_style == 'Default':
                    reply = f'<{author}> {await clean_message(message)}'
                await send(reply, '@a[tag=!off]')

    async def _d_send_messages():
        '''The function running in a loop sending the Minecraft messages in the Discord Chat'''
        global webhook_request, mc_only_synced_accounts
        while True:
            for message in m_messages:
                if enable_webhooks and message['sender'] in loaded_accounts['synced_webhooks']:
                    if not await minecraft_clean_message(message["message"]) == False:
                        await send_webhook(loaded_accounts['synced_webhooks'][message['sender']], await minecraft_clean_message(message["message"]))
                    m_messages.remove(message)
                elif not mc_only_synced_accounts:
                    if not await minecraft_clean_message(message["message"]) == False:
                        await channel.send(f'**<{message["sender"]}>** {await minecraft_clean_message(message["message"])}')
                    m_messages.remove(message)

            if webhook_request != False:
                #---Get Values---
                guild = channel.guild
                user = loaded_accounts['pending_webhooks'].get(webhook_request)
                member = discord.utils.get(guild.members, name=user['discord_tag'])
                
                #---Create Webhook---
                try:
                    webhook = await channel.create_webhook(name=user['discord_name'], avatar=requests.get(member.avatar.url).content, reason=dc_wh_reason)
                except:
                    await send(f'§l§8System §r§7: {mc_wh_creation_failed}§r', user['minecraft_name'])
                loaded_accounts.get('synced_webhooks').update(
                    {f'{user["minecraft_name"]}': f'{webhook.url}'})
                
                #---Create Synced Name---
                loaded_accounts.get('synced_names').update({user['discord_tag']: user['minecraft_name']})

                #---Delete request and save
                loaded_accounts.get('pending_webhooks').pop(webhook_request)
                save_accounts()
                webhook_request = False
            
            #---Wait for check_interval amount of seconds---
            await asyncio.sleep(check_interval)

    async def status():
        '''The function that sets the bot status to some random message every 15 seconds'''
        counter = 0
        #---Wait until the WebSocket is connected---
        while not running:
            await asyncio.sleep(1)
            
        #---Loop---
        while True:
            #---Increase the counter by 1 and make sure it doesn't go other 5---
            counter += 1
            counter %= 5

            #---Set the different statuses---
            if counter == 1:
                #"Minecraft Highlander"
                await bot.change_presence(activity=discord.Game(name="Minecraft Highlander"))
                
            elif counter == 2:
                #Pick a random user and "watch it"
                members = await send('/list', response=True)
                members = members.split(':')[1].splitlines()
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=members[random.randint(0, len(members) - 1)]))
                
            elif counter == 3:
                #Discord Link
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="https://discord.gg/KwgtbJFpk4"))
                
            elif counter == 4:
                #The amount of users online
                members = await send('/list', response=True)
                members = members.split(':')[0]
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=members))

            elif counter == 5:
                #Listening to "Swims Schreie"
                await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="Swims Schreie"))
            
            #---Wait 15 seconds---
            await asyncio.sleep(15)


    async def send_webhook(webhook_url, message):
        '''A simple function that sends something with a WebHook\n
        Example: send_webhook('https://api.discord...', 'Hello World')'''
        await AsyncDiscordWebhook(url=webhook_url, content=message).execute()

    async def clean_message(message):
        '''A function 'cleaning' the given message (!!!Only works when a Discord message object is given!!!)\n
        Example: The message is 'Hello :flushed: https://www.google.de'\nclean_message(message) -> Hello \nImportant: It only cleans the blocked things, as defined in the settings.'''
        string = message.content

        #---Block Emojis---
        if not allow_emojis:
            if string != remove_emojis(string):
                #await error(message, '3️⃣', 'warn')
                string = remove_emojis(string)
        
        #---Block Links---
        if not allow_links:
            if string != re.sub(r'http\S+', '', string):
                #await error(message, '4️⃣', 'warn')
                string = re.sub(r'http\S+', '', string)

        #---Block long messages---
        if max_characters > -1 and len(string) > max_characters:
            #await error(message, '2️⃣', 'crit')
            return False
        
        #---Block emty messages---
        if string.replace(' ', '') == '':
            #await error(message, '1️⃣', 'crit')
            return False
        else:
            return string

    async def minecraft_clean_message(string):
        '''Cleans the given string (for Minecraft)'''

        #---Block long messages---
        if max_characters > -1 and len(string) > max_characters:
            return False
        
        #---Block Pings---
        if block_pings != 'disabled':
            if block_pings == 'all':
                string = re.sub(
                    r'<@.*?>', '', string).replace('@everyone', '').replace('@here', '')
        if string.replace(' ', '') == '':
            return False
        else:
            return string

    loop_discord.create_task(_d_send_messages())

    #---Runs the bot---
    try:
        bot.run(token)
    except discord.errors.LoginFailure:
        #If the login fails, throw an error
        print_color(dc_login_error)
        ask_user_exit()


def main():
    '''The function starting the setup and the 2 threads for Minecraft and Discord'''
    setup()
    mc_thread = threading.Thread(target=asyncio.run, args=(init_websocket(),))
    dc_thread = threading.Thread(target=discord_bot)
    mc_thread.start()
    dc_thread.start()
    mc_thread.join()
    dc_thread.join()


main()
