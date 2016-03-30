# Bridge that links a discord chatroom with a twitch chatroom

import discord
import yaml
import asyncio
import sys
import random
import copy
import os


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
            yield from displayHelp(message)
        elif (command.startswith('!thanks')):
            yield from thanksCommand(message)
        elif (command.startswith('!commandadd')):
            yield from addCommand(message)
        elif (command.startswith('!commanddel')):
            yield from delCommand(message)
        elif (command.startswith('!commandrestore')):
            yield from restoreCommand(message)
        elif (command.startswith('!commanddesc')):
            yield from descCommand(message)
        elif (command.startswith('!source')):
            yield from sourceCommand(message)
        elif (command[1:] in commands): # if config file has command
            yield from runCommand(commands[command[1:]], message.channel)
    return

@asyncio.coroutine
def displayHelp(message):
    channel = message.channel
    commands = config["Commands"]
    helpMessage = """{0}, a chatbot for {1} - usage \"!<command>\"

Commands:
\t!help - Displays this help page
\t!help all - Sends you a message with all commands
\t!stream - Displays a list of streamers
\t!thanks - Thanks a random online member for a stream
\t!source - Gives a link to the source code of {0}\
""".format(client.user.name, config["Server Data"]["Server Name"])
    if message.content.startswith('!help all'):
        helpMessage +="""\
\t!streamadd - Adds a streamer to the streamers list (Mod Only)
\t!streamdel - Removes a streamer from the streamers list (Mod Only)
\t!commandadd - Adds a command (Mod Only)
\t!commanddel - Deletes a command (Mod Only)
\t!commanddesc - Adds a description to the command (Mod Only)
\t!commandrestore - Restores a command from backup (Mod Only)
\t!commandimportant - Sets whether a command is displayed on default help (Mod Only)"""
        for com in commands:
            helpMessage += "\n\t!" + com;
            if "Description" in commands[com]:      #Append command description
                helpMessage += "- " + commands[com]["Description"]
        yield from client.send_message(message.author, helpMessage)
    else:
        # Add important commands to default list
        for com in commands:
            if safeConfigLookup(commands[com], "Important", False):
                helpMessage += "\n\t!" + com;
                if "Description" in commands[com]:      #Append command description
                    helpMessage += "- " + commands[com]["Description"]
        yield from client.send_message(channel, helpMessage)

@asyncio.coroutine
def thanksCommand(message):
    text = "Thanks for the stream {0}!"
    userlist = list(message.server.members)
    user = random.choice(userlist)
    userlist.remove(user)
    while(user.status != discord.Status.online):
        user = random.choice(userlist)
        userlist.remove(user)
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
                    yield from client.send_message(message.channel,\
                        helpText + "\n\t**Error: Streamer already added.**")
                    return
            config["Streamers"][streamerName] = streamerLink
            rewriteConfig()
            yield from client.send_message(message.channel,\
                streamerName + " added to stream list.")
        else:
            yield from client.send_message(message.channel,\
                helpText + "\n\t**Error: You are not allowed to add streamers.**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel,\
            helpText + "\n\t**Error: Not enough arguments.**")
        
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
                    yield from client.send_message(message.channel,\
                        streamer + " removed from stream list.")
                    return
            yield from client.send_message(message.channel,\
                helpText + "\n\t**Error: Streamer doesn't exist.**")
        else:
            yield from client.send_message(message.channel,\
                helpText + "\n\t**Error: You are not allowed to remove streamers.**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel,\
            helpText + "\n\t**Error: Not enough arguments.**")

@asyncio.coroutine
def addCommand(message):
    helpText = """\
!commandadd - Mod only, adds a command to the command list. If command exists, adds option.
\t- Usage \"!commandadd commandName Command Text"""
    msgList = message.content.split(' ')
    if (len(msgList) >= 3):
        if (isMod(message.author)):
            commandName = msgList[1]
            commandText = message.content.split(' ', 2)[2]
            if commandName in config["Commands"]: # Check if the command has already been added
                config["Commands"][commandName]["Options"].append(commandText)
                rewriteConfig()
                yield from client.send_message(message.channel,\
                    "Option added for " + commandName + '.')
            else:
                commandOptions = [commandText]
                config["Commands"][commandName] = {"Important": False,
                    "Options": commandOptions,
                    "Author": message.author.name}
                rewriteConfig()
                yield from client.send_message(message.channel,\
                    commandName + " added to command list.")
        else:
            yield from client.send_message(message.channel,\
               helpText + "\n\t**Error: You are not allowed to add commands.**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel,\
               helpText + "\n\t**Error: Not enough arguments.**")

@asyncio.coroutine
def delCommand(message):
    helpText = """\
!commanddel - Mod only, removes a command from the command list
\t- Usage \"!commanddel commandName\""""
    msgList = message.content.split(' ')
    if (len(msgList) == 2):
        if (isMod(message.author)): 
            commandName = msgList[1]
            if commandName in config["Commands"]: # Check if the command is in the list
                # Back up command before deleting
                if commandName in config["Deleted Commands"]:
                    del(config["Commands"][commandName])
                    rewriteConfig()
                    yield from client.send_message(message.channel,\
                        ("{0} removed from command list, backup not saved."\
                            + " ({0} already in backup)").format(commandName))
                else:
                    # No backup already exists
                    config["Deleted Commands"][commandName] =\
                        config["Commands"].pop(commandName)
                    config["Deleted Commands"][commandName]["Deleted By"] =\
                        message.author.name
                    rewriteConfig()
                    yield from client.send_message(message.channel,\
                        commandName + " removed from command list, backup saved")
            else:
                yield from client.send_message(message.channel,\
                    helpText + "\n\t**Error: Command doesn't exist.**")
        else:
            yield from client.send_message(message.channel,\
                helpText + "\n\t**Error: You are not allowed to remove commands.**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel,\
            helpText + "\n\t**Error: Too many arguments.**")

@asyncio.coroutine
def restoreCommand(message):
    helpText = """\
!commandrestore - Mod only, restores a command from the deleted command list
\t- Usage \"!commandrestore commandName\""""
    msgList = message.content.split(' ')
    if (len(msgList) == 2):
        if (isMod(message.author)): 
            commandName = msgList[1]
            if commandName in config["Deleted Commands"]: # Check if the command is in the list
                if commandName in config["Commands"]:
                    yield from client.send_message(message.channel,\
                        "**Error: Command already exists**")
                else:
                    # Command doesn't already exist
                    config["Commands"][commandName] =\
                        config["Deleted Commands"].pop(commandName) 
                    config["Commands"][commandName]["Restored By"] = message.author.name
                    rewriteConfig()
                    yield from client.send_message(message.channel,\
                        commandName + " restored from backup.")
            else:
                yield from client.send_message(message.channel,\
                    helpText + "\n\t**Error: Command doesn't exist in backup.**")
        else:
            yield from client.send_message(message.channel,\
                helpText + "\n\t**Error: You are not allowed to restore commands.**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel,\
            helpText + "\n\t**Error: Too many arguments.**")

@asyncio.coroutine
def importantCommand(message):
    helpText = """\
!commandimportant - Mod only, sets if a command is shown on the default !help menu
\t- Usage \"!commandimportant commandName [True | False]\""""
    msgList = message.content.split(' ')
    if (len(msgList) == 3):
        if (isMod(message.author)): 
            if (msgList[2].lower() == "true" or msgList[2].lower() == "false"):
                commandName = msgList[1]
                if commandName in config["Commands"]: # Check if the command is in the list
                    if (msgList[2].lower() == "true"):
                        b = True
                    else:
                        b = False
                    config["Commands"][command]["Important"] = b
                    rewriteConfig()
                    yield from client.send_message(message.channel,\
                        command + "'s importance set to " + b)
                else:
                    # Command not found
                    yield from client.send_message(message.channel,\
                        helpText + "\n\t**Error: {0} not found.**".format(commandName))
            else:
                yield from client.send_message(message.channel,\
                    helpText + "\n\t**Error: Value must be either true or false")
        else:
            yield from client.send_message(message.channel,\
                helpText + "\n\t**Error: You are not allowed to change commands.**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel,\
            helpText + "\n\t**Error: Wrong number of arguments.**")

@asyncio.coroutine
def descCommand(message):
    helpText = """\
!commanddesc - Mod only, changes the description of a command.
\t- Usage \"!commanddesc commandName Command Description\""""
    msgList = message.content.split(' ')
    if (len(msgList) >= 3):
        if (isMod(message.author)): 
            commandName = msgList[1]
            if commandName in config["Commands"]: # Check if the command is in the list
                # Command Found, time to set description
                desc = message.content.split(' ', 2)[2]
                config["Commands"][commandName]["Description"] = desc
                rewriteConfig()
                yield from client.send_message(message.channel,\
                    commandName + "'s description set to: " + desc)
            else:
                # Command not found
                yield from client.send_message(message.channel,\
                    helpText + "\n\t**Error: {0} not found.**".format(commandName))
        else:
            yield from client.send_message(message.channel,\
                helpText + "\n\t**Error: You are not allowed to change commands.**")
    elif (len(msgList) == 1):
        yield from client.send_message(message.channel, helpText)
    else:
        yield from client.send_message(message.channel,\
            helpText + "\n\t**Error: Wrong number of arguments.**")

def isMod(user):
    superUsers = config["Server Data"]["Mod Roles"]
    uroles = []
    
    for role in user.roles:
        uroles.append(role.name.lower())
    
    for role in superUsers:
        lrole = role.lower()
        if lrole == "everyone":
            print("Granting access to {0} as everyone")
            return True
        if lrole in uroles:
            print("Granting access to {0} as role: {1}".format(user.name, lrole))
            return True
    print("Returning false, {0} denied access. Bad roles: ").format(user.name) 
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
    yield from client.send_message(message.channel,\
        streamHelp + "\n\n\t**Error: Streamer not found**")
        
@asyncio.coroutine
def sourceCommand(message):
    reply = "{0}'s source code is available at http://github.com/mtvjr/WaifuBot"\
        .format(client.user.name)
    yield from client.send_message(message.channel, reply)

def genConfig():
    modRoles = ["Admin", "Mod", "Moderator"]
    loginData = {"Email": "email@email.ext", "Password": "pAssw0rd"}
    serverData = {"Server Name": "Discord Server", "Mod Roles": modRoles,\
        "Server ID": "135531470562394112"}
    streamers = {"Joe": "Joe's Website", "Megan": "Megan's Website"}
    optionsHi = ["Hello There!", "Howdy"]
    command = {"Options": optionsHi, "Description": "Says hello", "Important": True}
    optionsBye = ["Goodbye!"]
    command2 = {"Options": optionsBye, "Description": "Says Goodbye", "Important": False}
    optionsKnock = ["Who's there?"]
    command3 = {"Options": optionsKnock, "Description": "Says Who's There?", "Important": False}
    commands = {"hi": command, "bye": command2}
    deletedCommands = {"Knock": command3}
    global config
    config = {"Login Data": loginData, "Server Data": serverData, "Streamers": streamers,\
        "Commands": commands, "Deleted Commands": deletedCommands}
    rewriteConfig()
    return

def rewriteConfig():
    f = open("config.yml", "w")
    yaml.dump(config, f, default_flow_style=False)

def setName(newName):
    if (os.name == "nt"):
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleA(str.encode(newName))
    else:
        sys.stdout.write("\x1b]2;{0}\x07".format(newName))

def safeConfigLookup(configDict, key, default):
    if key not in configDict:
        configDict[key] = default
        rewriteConfig()
    return configDict[key]

if __name__ == "__main__":
    if (len(sys.argv) > 1):
        #Check arguments
        if (sys.argv[1] == "--generate-config"):
            genConfig()
            exit()
    
    setName("Waifu Bot")
    config = yaml.safe_load(open("config.yml"))
    loginData = config["Login Data"]
    client.run(loginData["Email"], loginData["Password"])
