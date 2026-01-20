#!/usr/bin/env python

import asyncio
import logging
import shutil
import socket
import tracemalloc

import configargparse
import discord

from slack_bolt.adapter.socket_mode.aiohttp import AsyncSocketModeHandler
from slack_bolt.async_app import AsyncApp

from markov import Markov
from time import time

logging.basicConfig(level=logging.INFO)

parser = configargparse.ArgParser(description="CodeBro: A triumph of machine over man")
parser.add_argument(
    "-c", "--config", is_config_file=True, help="Path to config file in yaml format"
)
parser.add_argument(
    "-d",
    "--discord_token",
    env_var="CB_DISCORD_TOKEN",
    help="This bot's discord bot token",
)
parser.add_argument(
    "--slack_bot_token",
    env_var="CB_SLACK_BOT_TOKEN",
    help="This bot's slack bot token (the one prefixed with \"xoxb-\" in \"OAuth Tokens for Your Workspace\" under \"OAuth & Permissions\")",
)
parser.add_argument(
    "--slack_app_token",
    env_var="CB_SLACK_APP_TOKEN",
    help="This bot's slack app token (the one prefixed with \"xapp-\" in \"App-Level Tokens\" under \"Basic Information\")",
)
parser.add_argument(
    "--local_server_port",
    type=int,
    help="Set a local listen port to enable a local server",
)
parser.add_argument(
    "-b",
    "--brain",
    env_var="CB_BRAIN",
    required=True,
    help="This bot's input brain as a YAML or newline-delimited text file, also used as the base name for rotated brains",
)
parser.add_argument(
    "-o",
    "--output",
    env_var="CB_OUTPUT",
    required=True,
    help="File for writing the real-time updated corpus",
)
parser.add_argument(
    "-n",
    "--name",
    env_var="CB_NAME",
    required=True,
    help="The name this bot will respond to in chats",
)
parser.add_argument(
    "-r",
    "--rotate",
    env_var="CB_ROTATE",
    required=False,
    action="store_true",
    help="Backup the brain and copy the output to the brain on SIGTERM",
)
parser.add_argument(
   "-u",
   "--user_map",
   env_var="USER_MAP",
   required=False,
   help="Discord-to-Slack user id map",
)
args = parser.parse_args()

discord_token = args.discord_token
slack_bot_token = args.slack_bot_token
slack_app_token = args.slack_app_token
user_map = args.user_map
bot_name = args.name

tracemalloc.start()

brain = Markov(args.brain, args.output, args.user_map, [bot_name])
snapshot = tracemalloc.take_snapshot()

snapshot.dump('mem_snapshot_new.dmp')
tracemalloc.stop()

intents = discord.Intents(guild_messages=True, message_content=True)
discord_client:discord.Client = None

def rotate_brain(the_brain: str, output: str):
    brain_backup = "{}.{}".format(the_brain, time())
    shutil.move(the_brain, brain_backup)
    shutil.move(output, the_brain)


def sanitize_and_tokenize(msg: str) -> list:
    msg_tokens = msg.split()
    for i in range(0, len(msg_tokens)):
        msg_tokens[i] = msg_tokens[i].strip("'\"!@#$%^&*().,/\\+=<>?:;").upper()
    return msg_tokens

def get_ten(is_slack) -> str:
    response = ""
    for i in range(0, 9):
        response += brain.create_response(slack=is_slack)
        response += "\n"
    return response

#**********************< SLACK & DISCORD STUFF>**************************#
if discord_token:
    discord_client = discord.Client(intents=intents)
else:
    discord_client = None

if discord_client:
    @discord_client.event
    async def on_ready():
        print("Logged in as {0.user}".format(discord_client))

    @discord_client.event
    async def on_message(message):
        if message.author == discord_client.user:
            return

        num_words_in_brain = len(brain.words)
        if num_words_in_brain >= (Markov.SIGNED_INT_MAX_VALUE * 0.95):
            await message.channel.send('Brain hurty. Brain almost full :sob:')
            return

            # print(f"Discord message from {message.author}: {message.content}")
        response = create_raw_response(message.content, False)
        if response and response.strip() != "":
            await message.channel.send(response)

if slack_bot_token:
    app = AsyncApp(token=slack_bot_token)
else:
    app = None
if app:
    @app.event("message")
    async def handle_slack_message(payload):
        response = create_raw_response(payload["text"], True)
        if response and response.strip() != "":
            await app.client.chat_postMessage(channel=payload["channel"], text=response)

    slack_socket_client = AsyncSocketModeHandler(app, slack_app_token)

    async def run_slack_app():
        await slack_socket_client.connect_async()
#**********************</SLACK & DISCORD STUFF>**************************#


def create_raw_response(incoming_message, is_slack):
    msg_tokens = sanitize_and_tokenize(incoming_message)
    if (bot_name.upper() in msg_tokens) or "TOWN" in msg_tokens:  # it's not _not_ a bug
        if "GETGET10" in msg_tokens:
            return get_ten(is_slack)
        else:
            return brain.create_response(incoming_message, learn=True, slack=is_slack)

# TODO: the local server should probably be a class and should probably be
# multi-threaded to handle simultaneous connections ... but this is expedient
# for quick local testing without Slack/Discord integration
#
# this will listen on a local server, if a port is specified.
# try connecting with netcat or something, like nc localhost <your port>
def run_local_server(port_num):
    host = "localhost"
    port = port_num
    prompt = "\nSay something: "
    print("Listening on port: " + str(port))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen(1)
        conn, addr = s.accept()
        with conn:
            print("Connection recieved from", addr)
            while True:
                conn.sendall(str.encode(prompt))
                data = conn.recv(1024)
                if not data:
                    break
                decoded_data = data.decode("utf-8")
                response = create_raw_response(decoded_data, False)
                if response:
                    response = bot_name + " " + "said: " + response
                    conn.sendall(str.encode(response))

# MAIN ----
basic_loop = asyncio.get_event_loop()
try:
    if args.local_server_port:
        run_local_server(port_num=args.local_server_port)
    if app:
        basic_loop.create_task(run_slack_app())
    if discord_client:
        basic_loop.create_task(discord_client.start(discord_token)),
    basic_loop.run_forever()
except KeyboardInterrupt:
    if args.rotate:
        rotate_brain(args.brain, args.output)
finally:
    basic_loop.close()
