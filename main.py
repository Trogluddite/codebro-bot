#!/usr/bin/env python

import asyncio
import json
import logging

import configargparse
import discord

from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.socket_mode.aiohttp import SocketModeClient
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.socket_mode.request import SocketModeRequest

from markov import Markov

logging.basicConfig(level=logging.INFO)

parser = configargparse.ArgParser(description='CodeBro: A triumph of machine over man.')
parser.add_argument('-c', '--config',
                    is_config_file=True,
                    help='Path to config file in yaml format')
parser.add_argument('-d', '--discord_token',
                    env_var="CB_DISCORD_TOKEN",
                    help="This bot's discord bot token.")
parser.add_argument('--slack_bot_token',
                    env_var="CB_SLACK_BOT_TOKEN",
                    help="This bot's slack bot token.")
parser.add_argument('--slack_app_token',
                    env_var="CB_SLACK_APP_TOKEN",
                    help="This bot's slack app token.")
parser.add_argument('-b', '--brain',
                    env_var="CB_BRAIN",
                    required=True,
                    help="This bot's brain as a YAML file.")
parser.add_argument('-n', '--name',
                    env_var="CB_NAME",
                    required=True,
                    help="The name this bot will respond to in chats.")
parser.add_argument('--skip_mp',
                    env_var="CB_SKIP_MP",
                    action="store_true",
                    help="Skip the multiprocess stuff that can hinder debugging.")
args = parser.parse_args()

discord_token = args.discord_token
slack_bot_token = args.slack_bot_token
slack_app_token = args.slack_app_token

bot_name = args.name
brain = Markov(args.brain, bot_name.upper(), args.skip_mp)

discord_client = discord.Client()


def sanitize_and_tokenize(msg: str) -> list:
    msg_tokens = msg.split()
    for i in range(0, len(msg_tokens)):
        msg_tokens[i] = msg_tokens[i].strip("\'\"!@#$%^&*().,/\\+=<>?:;").upper()
    return msg_tokens


def get_ten() -> str:
    response = ""
    for i in range(0, 9):
        response += brain.create_response()
        response += '\n'
    return response


@discord_client.event
async def on_ready():
    print('Logged in as {0.user}'.format(discord_client))


def create_raw_response(incoming_message):
    msg_tokens = sanitize_and_tokenize(incoming_message)
    if bot_name.upper() in msg_tokens:
        if "GETGET10" in msg_tokens:
            return get_ten()
        else:
            return brain.create_response(incoming_message, True)


@discord_client.event
async def on_message(message):
    if message.author == discord_client.user:
        return
        # print(f"Discord message from {message.author}: {message.content}")
    response = create_raw_response(message.content)
    if response and response.strip() != "":
        await message.channel.send(response)


async def process(client: SocketModeClient, req: SocketModeRequest):
    if req.type == "events_api":
        # Apparently we want to acknowledge whatever this is
        some_ack_response = SocketModeResponse(envelope_id=req.envelope_id)
        await client.send_socket_mode_response(some_ack_response)

        if req.payload["event"]["type"] == "message" \
            and req.payload["event"].get('subtype') is None:

            response = create_raw_response(req.payload["event"]["text"])
            if response and response.strip() != "":
                await client.web_client.chat_postMessage(
                    channel=req.payload["event"]["channel"],
                    text=response
                )

slack_client = SocketModeClient(
    app_token=slack_app_token,
    web_client=AsyncWebClient(token=slack_bot_token)
)

slack_client.socket_mode_request_listeners.append(process)

basic_loop = asyncio.get_event_loop()
basic_loop.create_task(slack_client.connect())
basic_loop.create_task(discord_client.start(discord_token)),
basic_loop.run_forever()
