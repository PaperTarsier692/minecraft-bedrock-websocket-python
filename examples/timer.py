'''A simple timer.'''

import re  # Filter Emojis, Commands
import json  # JSON Data for sending and recieving WebSocket Data
import time
import asyncio  # Async Code execution througout the entire project
import datetime
import threading
import websockets  # Websockets for Minecraft
from uuid import uuid4  # Generate UUIDs for Minecraft
from requests import get  # Get the Public IP


global public, port, self_host

public = True
# Uses your Public IP and makes the WebSocket available for anyone; Default: False

port = 6464
# Sets the port to be used for the WebSocket; Default: 6464

self_host = True
# If the WebSocket is connected to a world hosted by the person who typed the command; Default: True


def cmd(command: str, arguments=None):
    '''A function for checking if a certain command was called in Minecraft\n
    Examples:\n
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
        return match
    return False


async def send(cmd: str, selector='@a', response=False):
    '''Send something in the MC chat using WebSockets\n
    Examples:\n
    await send('Hello World') => Sends 'Hello World' into the chat (with tellraw)\n
    await send('/list', response=True) -> 'There are 1/8 players online: ...'\n
    await send('Hello Paper', selector='@PaperTarsier692') -> Sends 'Hello Paper' to @PaperTarsier692\n
    await send('Pong', selector='@sender') -> Sends the message to the user who sent the command (Only works when executing it on a command)
    '''
    uuid = uuid4()
    msg = {"header": {"version": 1, "requestId": f'{uuid}', "messagePurpose": "commandRequest",
                      "messageType": "commandRequest"}, "body": {"version": 1, "commandLine": cmd, "origin": {"type": "player"}}}
    if cmd.startswith('/') == False:
        if selector == '@sender':
            selector = msg_b.get('sender')
        if self_host == True:
            msg['body']['commandLine'] = "/tellraw " + \
                selector + '{"rawtext":[{"text":"' + cmd + '"}]}'
        else:
            msg['body']['commandLine'] = "/msg " + selector + ' ' + cmd
    await websocket_var.send(json.dumps(msg))
    if response:
        try:
            return await asyncio.wait_for(_wait_for_response(uuid), timeout=True)
        except asyncio.TimeoutError:
            print('Timeout waiting for response from Minecraft')
            return None


async def _wait_for_response(uuid):
    '''A helper function used by send() to wait for a response from Minecraft'''
    global msg
    while True:
        resp_json = msg
        if 'header' in resp_json and 'requestId' in resp_json['header'] and resp_json['header']['requestId'] == str(uuid):
            return resp_json['body']['statusMessage']


async def mineproxy(websocket):
    '''The function running the WebSocket'''
    global websocket_var, msg, msg_b, running, timers
    websocket_var = websocket
    await websocket.send(json.dumps({"body": {"eventName": "PlayerMessage"}, "header": {"requestId": f'{uuid4()}', "messagePurpose": "subscribe", "version": 1, "messageType": "commandRequest"}}))
    # This is sent to Minecraft to subscribe to Chat messages
    print('Connected')
    running = True
    timers = {}
    async for msg in websocket:
        msg = json.loads(msg)
        msg_b = msg['body']

        if msg['header'].get('eventName') == 'PlayerMessage':
            if cmd('!timer start user', 'text'):
                timers[match.group(1).replace('@', '')] = 0
                await send('Los!', match.group(1).replace('@', ''))
            elif cmd('!timer end user', 'text'):
                timers.pop(match.group(1).replace('@', ''))
            elif cmd('!timer start'):
                timers[msg_b.get('sender')] = 0
                await send('Los!', '@sender')
            elif cmd('!timer end'):
                timers.pop(msg_b.get('sender'))


async def init_websocket():
    '''Initialises the WebSocket and runs some misc things, like copying the command in the clipboard'''
    # ---Run on private/public IP---
    if public:
        # If the public IP address gets selected, get it with the ipify API and print it
        ip = '0.0.0.0'
        public_ip = get('https://api.ipify.org').content.decode('utf8')
        print(f'Running WebSocket @ {public_ip}:{port}')
    else:
        # If the private IP address gets selected, use the localhost as IP
        ip = 'localhost'
        print(f'Running WebSocket @ localhost:{port}')

    # ---Start the WebSocket listener---
    await websockets.serve(mineproxy, ip, port)
    print('Ready')
    await asyncio.Future()


def timer():
    global running
    running = False
    while not running:
        time.sleep(1)
    global timers
    while True:
        for key, value in timers.items():
            timers[key] = value + 1
            minutes, seconds = divmod((value + 1), 60)
            hours, minutes = divmod(minutes, 60)
            zeit = "§4{:02d}§r:§e{:02d}§r:§a{:02d}".format(
                hours, minutes, seconds)
            asyncio.run(send(f'/title {key} actionbar {zeit}'))
        time.sleep(1)


def main():
    '''The function starting the setup and the 2 threads for Minecraft and Discord'''
    mc_thread = threading.Thread(target=asyncio.run, args=(init_websocket(),))
    timer_thread = threading.Thread(target=timer)
    mc_thread.start()
    timer_thread.start()
    mc_thread.join()
    timer_thread.join()


main()
