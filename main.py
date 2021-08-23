#!/usr/bin/env python
import asyncio
import json

import aiohttp
import configargparse
import discord

from markov import Markov

parser = configargparse.ArgParser(description='CodeBro: A triumph of machine over man.')
parser.add_argument('-c', '--config',
                    is_config_file=True,
                    help='Path to config file in yaml format')
parser.add_argument('-d', '--discord_token',
                    env_var="CB_DISCORD_TOKEN",
                    required=True,
                    help="This bot's discord bot token.")
parser.add_argument('-s', '--slack_token',
                    env_var="CB_SLACK_TOKEN",
                    required=True,
                    help="This bot's slack bot token.")
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
slack_token = args.slack_token
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
    response = create_raw_response(message.content)
    await message.channel.send(response)


async def slack_api_call(token, method, data=None):
    async with aiohttp.ClientSession() as session:
        form = aiohttp.FormData(data or {})
        form.add_field('token', token)
        async with session.post('https://slack.com/api/{0}'.format(method), data=form) as response:
            assert 200 == response.status, ('{0} with {1} failed.'.format(method, data))
            return await response.json()


async def slack_converse(token):
    rtm = await slack_api_call(token, "rtm.start")
    assert rtm['ok'], f"Error starting Slack RTM: {rtm}."

    async with aiohttp.ClientSession() as session:
        async with session.ws_connect(rtm["url"]) as ws:
            async for msg in ws:

                msg_obj = json.loads(msg.data)

                print("==========")
                print(msg_obj)
                if 'type' in msg_obj and msg_obj['type'] == 'message':
                    print(f"Received a message on channel {msg_obj['channel']} from user {msg_obj['user']} containing \"{msg_obj['text']}\".")
                    # await ws.send_str('{"type":"message", "channel":"D02BW1P4L7P", "text":"Ok, thanks much."}')

                    # assert msg.tp == aiohttp.MsgType.text
                    msg_channel = msg_obj['channel']
                    msg_text = msg_obj['text']

                    response = create_raw_response(msg_text)
                    slack_response = {
                        "type":"message",
                        "channel":msg_channel,
                        "text":response
                    }
                    await ws.send_str(json.dumps(slack_response))

tasks = [
    discord_client.start(discord_token),
    slack_converse(slack_token)
]
tasks_group = asyncio.gather(*tasks, return_exceptions=True)
basic_loop = asyncio.get_event_loop()
basic_loop.run_until_complete(tasks_group)
