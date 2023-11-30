# minecraft-bedrock-websocket-python

A Python project for making and handling a connection with Minecraft. 
The code for modification (primarily adding commands) is the standard.py file, some small examples like a Ping-Pong and Timer command can be found in the examples directory.
Discord Sync is also a modified version of the standard.py file, has a config system, logs, lang files and its purpose is to sync the Minecraft Chat with a Discord Channel.

# A small Explanation

Minecraft allows a connection to a WebSocket server using its /connect or /wsserver command, but only if you are the host of the world. If you have your WebSocket connected the connection stays even if you leave the world and join a multiplayer world/realm (and maybe even some servers), but then it only has access to your messages and commands you can execute.

As soon as the connection is established, the code sends a message to subscribe to chat messages (you can subscribe to other events, but I haven't tested this succesfully), and after that you can do everything you want with those messages, log them, send them in Discord, or make custom commands, the main purpose of this project.

You can also send messages/commands in the Chat, as if being a player (with "External" as name), but in self hosted worlds tellraw is a much cleaner approach to send messages.

I hope my try to explain this a little bit may help you, and I hope my English is understandable, if you have any questions you can contact me over Discord @papertarsier .
