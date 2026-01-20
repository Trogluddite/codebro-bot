# codebro-bot
a toy markov-bot project; behold: stream-of-consciousness python

# Run a local server
This is useful for testing the basic functionality and interacting with the bot, without connecting to Slack or Discord.

## Start up:
Run `main.py`, with args to specify the input file ('brain'), output file (a log of recorded messages), the bot's name, and a local port.
For example:
```
./main.py --local_server_port 9966 --brain blah.yaml --output meh.brain --name dumdum
```

For blank-slate testing, you need to create a seed brain with at least two tokens
```.
[<START>, hi, hello, <STOP>]
```

## Connecting & interacting
Once the server is running, you can background the process or open up another terminal, and connect to the port you opened with `nc`.

The Bot will respond when whatever name you've given it is called, in the same manner as a connection to Slack or Discord, and should start learning from your conversation:
```
> nc localhost 9966

Say something: hello dumdum
dumdum said: hi hello
Say something: dumdum, learn some things
dumdum said: hi hello
Say something: yes dumdum we covered that
dumdum said: hi hello
Say something: try something new dumdum
dumdum said: learn some things
```

## persistence & logging
Everything the bot learns will be appended to the file you specified in `--output`

The input file needs to have some basic pickling; a convenience script, `make_yaml.py`, will convert any file of phrases into a new consumable brain for the bot.

This example takes the --output specified in the above example, and prepares it for a new instance of the bot:
```
 ./make_yaml.py --garbage-in meh.brain --garbage-out blah.yaml
```

You can tail the output file to see what the bot is learning in real-time.

# Codebro Resurrect

### **Create a Slack app**:

Head over to https://api.slack.com/apps.

Under "Your Apps", select "Create an App," then select "From scratch" from the next prompt.

Give your app a name and select a workspace to install the app.


### **Get an app token**:

Find "Socket Mode" in the left-hand Settings menu. Enable socket mode. This will generate an app token, the first of two tokens you'll need. Copy and save the app token.

### **Add a bot token scope**:

Before we can install the app to a workspace and get our bot token, we need to add a bot token OAuth scope. Find "OAuth & Permissions" in the left-hand Features menu. Scroll down to "Scopes" and add scope "channels:read" and "chat:write". Now the app has permission to view basic information about public channels in a workspace.

### **Install to Workspace & bot token**:

At the top of the page, the "Install to Workspace" button should be green. Go ahead and install the app to a workspace. Then, head back to "Oauth & Permissions." You should see your bot token at the top of the page. Copy and save the token.

### **Event subscriptions**:

Find "Event Subscriptions" in the left-hand Features menu. Enable event subscriptions. Then, select "Subscribe to bot events" and add:

    - message:im
    - message:groups
    - message:channels
    - message:mpim

Save your changes. You should see a prompt to reinstall your app. Go ahead and reinstall.

### **Slash commands and direct messaging**:

Find "App Home" in the left-hand Features menu and check the box that allows users to send Slash commands and messages from the messages tab to your app.
