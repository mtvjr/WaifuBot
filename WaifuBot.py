# Bridge that links a discord chatroom with a twitch chatroom

import discord
import yaml
import asyncio
import sys
import random

config = dict()

client = discord.Client()

@client.event
@asyncio.coroutine
def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
    print('------')
    serverID = config["Login Data"]["Server ID"]
    return
    
@client.event
@asyncio.coroutine
def on_message(message):
    if message.author == client.user:
        return

    if (message.server.id != config["Login Data"]["Server ID"]):
        print("Found message on " + message.server.id)
        return
    

    print(config["Login Data"]["Server Name"] + " Message Found")
    command = message.content.split(' ')[0]
    if (command.startswith('!')):
        commands = config["Commands"]
        if (command.startswith('!stream')):
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
\t!stream <streamer> - Displays a link to the streamer's page
\t!thanks - Thanks a random online member for a stream.""".format(config["Login Data"]["Server Name"])
    for com in commands:
        helpMessage += "\n\t!{0} - {1}".format(com, commands[com]["Description"])
    yield from client.send_message(channel, helpMessage)

@asyncio.coroutine
def thanksCommand(message):
    text = "Thanks {0} for the stream!"
    user = random.sample(set(message.server.members), 1)[0]
    yield from client.send_message(message.channel, text.format(user.name))

@asyncio.coroutine
def runCommand(command, channel):
    message = random.sample(command["Options"], 1)[0]
    yield from client.send_message(channel, message)
    return

@asyncio.coroutine
def displayHelp(channel):
    commands = config["Commands"]
    helpMessage = """WaifuBot, a chatbot for {0} - usage \"!<command>\"

Commands:
\t!help - Displays this help page
\t!stream - Displays a list of streamers
\t!stream <streamer> - Displays a link to the streamer's page""".format(config["Login Data"]["Server Name"])
    for com in commands:
        helpMessage += "\n\t!{0} - {1}".format(com, commands[com]["Description"])
    yield from client.send_message(channel, helpMessage)
        

@asyncio.coroutine
def runCommand(command, channel):
    message = random.sample(command["Options"], 1)[0]
    yield from client.send_message(channel, message)
    
    
@asyncio.coroutine
def streamCommand(message): 
    streamTemplate = "{0} streams at {1}"
    streamers = config["Streamers"]
    streamHelp = """\
!stream - Usage \"!stream <streamer>\"

The added streamers are:"""   

    for streamer in streamers:
        streamHelp += "\n\t{0}".format(streamer)
    
    lis = message.content.split(' ')
    if (len(lis) == 1):
        yield from client.send_message(message.channel, streamHelp)
        return
    
    streamer = lis[1]
    
    if streamer in streamers:
        reply = "{0} streams at {1}".format(streamer, streamers[streamer])
        yield from client.send_message(message.channel, reply)
    else:
        print("Streamer not found: " + streamer)
        yield from client.send_message(message.channel, streamHelp)
        

def loadConfig(fileName):
    return yaml.load(open(fileName))

def genConfig():
    f = open("config.yml", "w")
    loginData = {"Email": "email@email.ext", "Password": "pAssw0rd", "Server ID": "135531470562394112", "Server Name": "Discord Server"}
    streamers = {"Joe": "Joe's Website", "Megan": "Megan's Website"}
    optionsHi = ["Hello There!", "Howdy"]
    command = {"Keyword": "hi", "Options": optionsHi, "Description": "Says hello"}
    optionsBye = ["Goodbye!"]
    command2 = {"Keyword": "bye", "Options": optionsBye, "Description": "Says Goodbye"}
    commands = {"hi": command, "bye": command2}
    conf = {"Login Data": loginData, "Streamers": streamers, "Commands": commands}
    yaml.dump(conf, f, default_flow_style=False)
    return

if __name__ == "__main__":
    if (len(sys.argv) > 1):
        #Check arguments
        if (sys.argv[1] == "--generate-config"):
            genConfig()
            exit()
    
    config = yaml.safe_load(open("config.yml"))
    loginData = config["Login Data"]
    client.run(loginData["Email"], loginData["Password"])
