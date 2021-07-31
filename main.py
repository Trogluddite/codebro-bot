#!/usr/bin/env python

import discord
from markov import Markov

token = open("auth.txt", "r").readline()
brain = Markov("codebro.yaml")
client = discord.Client()


def sanitize_and_tokenize(msg):
    msg_tokens = msg.split()
    for i in range(0, len(msg_tokens)):
        msg_tokens[i] = msg_tokens[i].strip("\'\"!@#$%^&*().,/\\+=<>?:;").upper()
    return msg_tokens


def getTen():
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
    if "CODEBRO" in msg_tokens:
        if "GETGET10" in msg_tokens:
            response = getTen()
        else:
            response = brain.create_response(message.content, True)
        await message.channel.send(response)


client.run(token)
