# codebro-bot
a toy markov-bot project; behold: stream-of-consciousness python

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
