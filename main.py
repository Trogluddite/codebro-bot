#!/usr/bin/env python
import asyncio

import configargparse
import discord
from markov import Markov

parser = configargparse.ArgParser(description='CodeBro: A triumph of machine over man.')
parser.add_argument('-c', '--config',
                    is_config_file=True,
                    help='Path to config file in yaml format')
parser.add_argument('-t', '--token',
                    env_var="CB_TOKEN",
                    required=True,
                    help="This bot's discord bot token.")
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

token = args.token
brain = Markov(args.brain, args.skip_mp)
name = args.name

client = discord.Client()


def sanitize_and_tokenize(msg: str) -> list:
    msg_tokens = msg.split()
    for i in range(0, len(msg_tokens)):
        msg_tokens[i] = msg_tokens[i].strip("\'\"!@#$%^&*().,/\\+=<>?:;").upper()
    return msg_tokens


def getTen() -> str:
    response = ""
    for i in range(0, 9):
        response += brain.create_response()
        response += '\n'
    return response


@client.event
async def on_ready():
    print('Logged in as {0.user}'.format(client))


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    msg_tokens = sanitize_and_tokenize(message.content)
    if name.upper() in msg_tokens:
        if "GETGET10" in msg_tokens:
            response = getTen()
        else:
            response = brain.create_response(message.content, True)
        await message.channel.send(response)


tasks = [client.start(token)]
tasks_group = asyncio.gather(*tasks, return_exceptions=True)

basic_loop = asyncio.get_event_loop()
basic_loop.run_until_complete(tasks_group)
