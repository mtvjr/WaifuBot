# Bridge that links a discord chatroom with a twitch chatroom

import discord
import yaml
import asyncio
import sys
import random
import os

if (os.name == "nt"):
    import ctypes
    ctypes.windll.kernel32.SetConsoleTitleA(b"WaifuBot")

config = dict()

client = discord.Client()

@client.event
@asyncio.coroutine
def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    serverID = config["Server Data"]["Server ID"]
    print("Allowing add commands from users in these roles:")
    for role in config["Server Data"]["Mod Roles"]:
        print("  "+role)
    print('-------------')
    return
    
@client.event
@asyncio.coroutine
def on_message(message):
    if message.author == client.user:
        return

    if (message.server.id != config["Server Data"]["Server ID"]):
        print("Found message on " + message.server.id)
        return
    

    print(config["Server Data"]["Server Name"] + " Message Found")
    command = message.content.split(' ')[0]
    if (command.startswith('!')):
        commands = config["Commands"]
        if (command.startswith('!streamadd')):
            yield from addStreamer(message)
        elif (command.startswith('!streamdel')):
            yield from delStreamer(message)
        elif (command.startswith('!stream')):
            yield from streamCommand(message)
        elif (command.startswith('!help') or command.startswith('!commands')):
            yield from displayHelp(message.channel)
        elif (command.startswith('!thanks')):
            yield from thanksCommand(message)
        elif (command[1:] in commands): # if config file has command
            yield from runCommand(commands[command[1:]], message.channel)
    return

@asyncio.coroutine
def displayHelp(channel):
    commands = config["Commands"]
    helpMessage = """WaifuBot, a chatbot for {0} - usage \"!<command>\"

Commands:
\t!help - Displays this help page
\t!stream - Displays a list of streamers
\t!stream streamerName - Displays a link to the streamer's page
\t!streamadd streamerName streamerLink - Adds a streamer to the streamers list (Mod Only)
\t!streamdel streamerName - Removes a streamer from the streamers list (Mod Only)
\t!thanks - Thanks a random online member for a stream""".format(config["Server Data"]["Server Name"])
    for com in commands:
        helpMessage += "\n\t!{0} - {1}".format(com, commands[com]["Description"])
    yield from client.send_message(channel, helpMessage)

@asyncio.coroutine
def thanksCommand(message):
    text = "Thanks for the stream {0}!"
    user = random.sample(set(message.server.members), 1)[0]
    yield from client.send_message(message.channel, text.format(user.name))

@asyncio.coroutine
def runCommand(command, channel):
    message = random.sample(command["Options"], 1)[0]
    yield from client.send_message(channel, message)
    return

@asyncio.coroutine
def addStreamer(message):
    helpText = """\
!streamadd - Mod only, adds a streamer to the streamers list
\t- Usage \"!streamadd streamerName streamerLink\""""
    msgList = message.content.split(' ')
    if (len(msgList) == 3):
        if (isMod(message.author)): 
            streamerName = msgList[1]
            streamerLink = msgList[2]
            for streamer in config["Streamers"]: # Check if the streamer has already been added
                if streamerName.lower() == streamer.lower():
                    yield from client.send_message(message.channel, helpText + "\n\t**Error: Streamer already added**")
                    return
            config["Streamers"][streamerName] = streamerLink
            rewriteConfig()
            yield from client.send_message(message.channel, streamerName + " added to stream list")
        else:
            yield from client.send_message(message.channel, helpText + "\n\t**Error: You are not allowed to add streamers**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel, helpText + "\n\t**Error: Not enough arguments**")
        
@asyncio.coroutine
def delStreamer(message):
    helpText = """\
!streamdel - Mod only, removes a streamer from the streamers list
\t- Usage \"!streamdel streamerName\""""
    msgList = message.content.split(' ')
    if (len(msgList) == 2):
        if (isMod(message.author)): 
            streamerName = msgList[1]
            for streamer in config["Streamers"]: # Check if the streamer is in the list
                if streamerName.lower() == streamer.lower():
                    del(config["Streamers"][streamer])
                    rewriteConfig()
                    yield from client.send_message(message.channel, streamer + " removed from stream list")
                    return
            yield from client.send_message(message.channel, helpText + "\n\t**Error: Streamer doesn't exist**")
        else:
            yield from client.send_message(message.channel, helpText + "\n\t**Error: You are not allowed to remove streamers**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel, helpText + "\n\t**Error: Not enough arguments**")

def isMod(user):
    superUsers = config["Server Data"]["Mod Roles"]
    uroles = []
    
    for role in user.roles:
        uroles.append(role.name.lower())
    
    for role in superUsers:
        lrole = role.lower()
        if lrole == "everyone":
            print("Granting access as everyone")
            return True
        if lrole in uroles:
            print("Granting access to role: " + role)
            return True
    print("Returning false, bad roles: ")  
    for role in uroles:
        print("  " + role)
    return False
    
@asyncio.coroutine
def streamCommand(message): 
    streamTemplate = "{0} streams at {1}"
    streamers = config["Streamers"]
    streamHelp = """\
!stream - Usage \"!stream <streamer>\"

The added streamers are:"""   

    streamerList = []
    for streamer in streamers:
        streamHelp += "\n\t{0}".format(streamer)
    
    lis = message.content.split(' ')
    if (len(lis) == 1):
        yield from client.send_message(message.channel, streamHelp)
        return
    
    streamer = lis[1].lower()
    
    for streamerKey in streamers:
        if streamer.startswith(streamerKey.lower()):
            reply = "{0} streams at {1}".format(streamerKey, streamers[streamerKey])
            yield from client.send_message(message.channel, reply)
            return
            
    print("Streamer not found: " + streamer)
    yield from client.send_message(message.channel, streamHelp + "\n\n\t**Error: Streamer not found**")
        
def genConfig():
    modRoles = ["Admin", "Mod", "Moderator"]
    loginData = {"Email": "email@email.ext", "Password": "pAssw0rd", "Server ID": "135531470562394112"}
    serverData = {"Server Name": "Discord Server", "Mod Roles": modRoles}
    streamers = {"Joe": "Joe's Website", "Megan": "Megan's Website"}
    optionsHi = ["Hello There!", "Howdy"]
    command = {"Keyword": "hi", "Options": optionsHi, "Description": "Says hello"}
    optionsBye = ["Goodbye!"]
    command2 = {"Keyword": "bye", "Options": optionsBye, "Description": "Says Goodbye"}
    commands = {"hi": command, "bye": command2}
    config = {"Login Data": loginData, "Server Data": serverData, "Streamers": streamers, "Commands": commands}
    rewriteConfig()
    return

def rewriteConfig():
    f = open("config.yml", "w")
    yaml.dump(config, f, default_flow_style=False)

if __name__ == "__main__":
    if (len(sys.argv) > 1):
        #Check arguments
        if (sys.argv[1] == "--generate-config"):
            genConfig()
            exit()
    
    config = yaml.safe_load(open("config.yml"))
    loginData = config["Login Data"]
    client.run(loginData["Email"], loginData["Password"])
