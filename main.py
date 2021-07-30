#!/usr/bin/python

import time
import json
import yaml
import random
from slackclient import SlackClient
from markov import Markov

SETTINGS_FILE = "settings.yaml"

token = ""
brain = Markov("codebro.yaml") 

def sanitize_and_tokenize(msg):
    msg_tokens = msg[0]["text"].split()
    for i in range(0, len(msg_tokens)):
        msg_tokens[i] = msg_tokens[i].strip("\'\"!@#$%^&*().,/\\+=<>?:;").upper()
    return msg_tokens

def getTen(channel):
    for i in range(0, 9):
        sc.rtm_send_message(channel, brain.create_response())

def load_settings(settings_file=SETTINGS_FILE):
    token = ""
    settings = {}
    with open(settings_file, "r") as sf:
        settings = yaml.safe_load(sf)
        token = settings.get("token")
    if not token:
        raise Exception("slack token is required!")
    return token

def get_msg(): 
    pass 

def handle_message(msg):
    pass


token = load_settings()
sc = SlackClient(token)
if sc.rtm_connect():
    print("###CONNECTED###")
else:
    print("Connect failed; invalid token?")

#set codebro ID
users = json.loads(sc.api_call("users.list"))
codebro_id = ''
for member in users["members"]:
    if member["name"] == "codebro":
        codebro_id = member["id"]

while True:
    current_wait = 1
    previous_wait = 1
    time.sleep(current_wait)
    try:
        msg = sc.rtm_read()
    except WebSocketConnectionClosedException:
        #simple fib. backoff
        tmp = current_wait
        current_wait = current_wait + previous_wait
        previous_wait = tmp
        print("failed; retrying in {time} seconds").format(time=current_wait)



    #this SEEMS to work? *shrug* 
    is_codebro = False
    if msg and ("reply_to" in msg[0]):
        is_codebro = True

    if msg and ("channel" in msg[0]):
        channel = msg[0]["channel"]
    if msg and ("text" in msg[0]):
        msg_tokens = sanitize_and_tokenize(msg)
        if ("CODEBRO" in msg_tokens) or (codebro_id in msg_tokens):
            if "GETGET10" in msg_tokens: 
                getTen(channel)
            else:
                if not (is_codebro):
                    response = brain.create_response( msg[0]["text"], True ) 
                    sc.rtm_send_message( channel, response )
