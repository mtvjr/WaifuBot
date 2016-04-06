# WaifuBot - A Discord bot capable of managing streamers and
# a command list

import discord
import yaml
import asyncio
import sys
import random
import os


config = dict()

client = discord.Client()


@client.event
@asyncio.coroutine
def on_ready():
    print("Logged in as")
    print(client.user.name)
    print(client.user.id)
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

    if message.server.id != config["Server Data"]["Server ID"]:
        print("Found message on {0} {1}.".format(
            message.server.id, message.author.id))
        return
    
    print("Found message on {0} by 2).".format(
        config["Server Data"]["Server Name"], message.author.id))
    command = message.content.split(' ')[0]
    if command.startswith('!'):
        commands = config["Commands"]
        if command.startswith('!streamadd'):
            yield from streamer_add(message)
        elif command.startswith('!streamdel'):
            yield from streamer_del(message)
        elif command.startswith('!stream'):
            yield from command_stream(message)
        elif command.startswith('!help')\
                or command.startswith('!commands'):
            yield from command_help(message)
        elif command.startswith('!thanks'):
            yield from command_thanks(message)
        elif command.startswith('!commandadd'):
            yield from command_add(message)
        elif command.startswith('!commanddel'):
            yield from command_delete(message)
        elif command.startswith('!commandrestore'):
            yield from command_restore(message)
        elif command.startswith('!commandimportant'):
            yield from command_important(message)
        elif command.startswith('!commanddesc'):
            yield from command_description(message)
        elif command.startswith('!source'):
            yield from command_source(message)
        elif command.startswith('!mentionable'):
            yield from command_mentionable(message)
        elif command[1:] in commands:  # if config file has command
            yield from command_run(commands[command[1:]],
                                   message.channel)
    return


@asyncio.coroutine
def command_help(message):
    channel = message.channel
    commands = config["Commands"]
    help_text = """{0}, a chat bot for {1} - usage \"!<command>\"

Commands:
\t!help - Displays this help page
\t!help all - Sends you a message with all commands
\t!stream - Displays a list of streamers
\t!thanks - Thanks a random online member for a stream
\t!source - Gives a link to the source code of {0}\
""".format(client.user.name, config["Server Data"]["Server Name"])
    if message.content.startswith('!help all'):
        help_text += """
\t!mentionable - Allows {0} to ping you
\t!streamadd - Adds a streamer to the streamers list (Mod Only)
\t!streamdel - Removes a streamer from the streamers list (Mod Only)
\t!commandadd - Adds a command (Mod Only)
\t!commanddel - Deletes a command (Mod Only)
\t!commanddesc - Adds a description to the command (Mod Only)
\t!commandrestore - Restores a command from backup (Mod Only)
\t!commandimportant - Sets whether a command is displayed on default\
help (Mod Only)"""
        for com in commands:
            help_text += "\n\t!" + com
            # Append command description
            if "Description" in commands[com]:
                help_text += " - " + commands[com]["Description"]
        yield from client.send_message(message.author, help_text)
    else:
        # Add important commands to default list
        for com in commands:
            if safe_config_lookup(commands[com], "Important", False):
                help_text += "\n\t!" + com
                # Append command description
                if "Description" in commands[com]:
                    help_text += " - " + commands[com]["Description"]
        yield from client.send_message(channel, help_text)


@asyncio.coroutine
def command_thanks(message):
    text = "Thanks for the stream {0}!"
    user_list = list(message.server.members)
    user = random.choice(user_list)
    user_list.remove(user)
    while user.status != discord.Status.online:
        user = random.choice(user_list)
        user_list.remove(user)
    if user.id in safe_config_lookup(config, "Mentionable Users", []):
        yield from client.send_message(message.channel,
                                       text.format(user.mention))
    else:
        yield from client.send_message(message.channel,
                                       text.format(user.name))


@asyncio.coroutine
def command_mentionable(message):
    help_text = """\
!mentionable - Allows {0} to ping you
\t- Usage \"!mentionable [ True | False ]\"""".format(client.user.name)
    msg_list = message.content.split(' ')
    user_id = message.author.id
    id_list = safe_config_lookup(config, "Mentionable Users", [])
    if len(msg_list) == 2:
        if msg_list[1].lower() == "true":
            if user_id in id_list:
                yield from client.send_message(
                    message.channel,
                    help_text +
                    "\n\t**Error: You are already mentionable**")
            else:
                id_list.append(user_id)
                rewrite_config()
                yield from client.send_message(
                    message.channel,
                    message.author.id +
                    " has been added to the mentionable list.")
        elif msg_list[1].lower() == "false":
            if user_id in id_list:
                id_list.remove(user_id)
                rewrite_config()
                yield from client.send_message(
                    message.channel,
                    message.author.id +
                    " has been removed from the mentionable list.")
            else:
                yield from client.send_message(
                    message.channel,
                    help_text +
                    "\n\t**Error: You are already not mentionable**")
        else:
            yield from client.send_message(
                message.channel,
                help_text +
                "\n\t**Error: Value must be true or false**")
    elif len(msg_list) == 1:
        yield from client.send_message(message.channel, help_text)
    else:
        yield from client.send_message(
            message.channel,
            help_text + "\n\t**Error: Wrong number of arguments.**")


@asyncio.coroutine
def command_run(command, channel):
    message = random.sample(command["Options"], 1)[0]
    yield from client.send_message(channel, message)
    return


@asyncio.coroutine
def streamer_add(message):
    help_text = """\
!streamadd - Mod only, adds a streamer to the streamers list
\t- Usage \"!streamadd streamer_name streamer_link\""""
    msg_list = message.content.split(' ')
    if len(msg_list) == 3:
        if is_mod(message.author):
            streamer_name = msg_list[1]
            streamer_link = msg_list[2]
            # Check if the streamer has already been added
            for streamer in config["Streamers"]:
                if streamer_name.lower() == streamer.lower():
                    yield from client.send_message(
                        message.channel, help_text +
                        "n\t**Error: Streamer already added.**")
                    return
            config["Streamers"][streamer_name] = streamer_link
            rewrite_config()
            yield from client.send_message(
                message.channel, streamer_name +
                " added to stream list.")
        else:
            yield from client.send_message(
                message.channel,
                help_text +
                "n\t**Error: You are not allowed to add streamers.**")
    elif len(msg_list) == 1:
        yield from client.send_message(message.channel, help_text)
    else:
        yield from client.send_message(
            message.channel,
            help_text + "n\t**Error: Not enough arguments.**")


@asyncio.coroutine
def streamer_del(message):
    help_text = """\
!streamdel - Mod only, removes a streamer from the streamers list
\t- Usage \"!streamdel streamer_name\""""
    msg_list = message.content.split(' ')
    if len(msg_list) == 2:
        if is_mod(message.author):
            streamer_name = msg_list[1]
            # Check if the streamer is in the list
            for streamer in config["Streamers"]:
                if streamer_name.lower() == streamer.lower():
                    del(config["Streamers"][streamer])
                    rewrite_config()
                    yield from client.send_message(
                        message.channel, streamer +
                        " removed from stream list.")
                    return
            yield from client.send_message(
                message.channel, help_text +
                "n\t**Error: Streamer doesn't exist.**")
        else:
            yield from client.send_message(
                message.channel,
                help_text +
                "n\t**Error: You are not allowed to remove streamers.**"
            )
    elif len(msg_list) == 1:
        yield from client.send_message(message.channel, help_text)
    else:
        yield from client.send_message(
            message.channel, help_text +
            "n\t**Error: Not enough arguments.**")


@asyncio.coroutine
def command_add(message):
    help_text = """\
!commandadd - Mod only, adds a command to the command list. If command\
exists, adds option.
\t- Usage \"!commandadd command_name Command Text"""
    msg_list = message.content.split(' ')
    if len(msg_list) >= 3:
        if is_mod(message.author):
            command_name = msg_list[1]
            command_text = message.content.split(' ', 2)[2]
            # Check if the command has already been added
            if command_name in config["Commands"]:
                config["Commands"][command_name]["Options"]\
                    .append(command_text)
                rewrite_config()
                yield from client.send_message(
                    message.channel,
                    "Option added for " + command_name + '.')
            else:
                command_options = [command_text]
                config["Commands"][command_name] =\
                    {"Important": False,
                     "Options": command_options,
                     "Author": message.author.name}
                rewrite_config()
                yield from client.send_message(
                    message.channel, command_name +
                    " added to command list.")
        else:
            yield from client.send_message(
                message.channel,
                help_text +
                "n\t**Error: You are not allowed to add commands.**")
    elif len(msg_list) == 1:
        yield from client.send_message(message.channel, help_text)
    else:
        yield from client.send_message(
            message.channel,
            help_text + "n\t**Error: Not enough arguments.**")


@asyncio.coroutine
def command_delete(message):
    help_text = """\
!commanddel - Mod only, removes a command from the command list
\t- Usage \"!commanddel command_name\""""
    msg_list = message.content.split(' ')
    if len(msg_list) == 2:
        if is_mod(message.author):
            command_name = msg_list[1]
            deleted_commands = safe_config_lookup(
                config, "Deleted Commands", dict())
            # Check if the command is in the list
            if command_name in config["Commands"]:
                # Back up command before deleting
                if command_name in deleted_commands:
                    del(config["Commands"][command_name])
                    rewrite_config()
                    yield from client.send_message(
                        message.channel,
                        ("{0} removed from command list, backup not " +
                         "saved. ({0} already in backup)")
                        .format(command_name))
                else:
                    # No backup already exists
                    deleted_commands[command_name] =\
                        config["Commands"].pop(command_name)
                    deleted_commands[command_name][
                        "Deleted By"] = message.author.name
                    rewrite_config()
                    yield from client.send_message(
                        message.channel,
                        command_name +
                        " removed from command list, backup saved")
            else:
                yield from client.send_message(
                    message.channel,
                    help_text + "\n\t**Error: Command doesn't exist.**")
        else:
            yield from client.send_message(
                message.channel,
                help_text +
                "\n\t**Error: You are not allowed to remove commands.**"
            )
    elif len(msg_list) == 1:
        yield from client.send_message(message.channel, help_text)
    else:
        yield from client.send_message(
            message.channel,
            help_text + "\n\t**Error: Too many arguments.**")


@asyncio.coroutine
def command_restore(message):
    help_text = """\
!commandrestore - Mod only, restores a command from the deleted command\
list
\t- Usage \"!commandrestore command_name\""""
    msg_list = message.content.split(' ')
    if len(msg_list) == 2:
        if is_mod(message.author):
            command_name = msg_list[1]
            # Check if the command is in the list
            if command_name in config["Deleted Commands"]:
                if command_name in config["Commands"]:
                    yield from client.send_message(
                        message.channel,
                        "**Error: Command already exists**")
                else:
                    # Command doesn't already exist
                    config["Commands"][command_name] =\
                        config["Deleted Commands"].pop(command_name)
                    config["Commands"][command_name]["Restored By"] =\
                        message.author.name
                    rewrite_config()
                    yield from client.send_message(
                        message.channel,
                        command_name + " restored from backup.")
            else:
                yield from client.send_message(
                    message.channel,
                    help_text +
                    "n\t**Error: Command doesn't exist in backup.**")
        else:
            yield from client.send_message(
                message.channel,
                help_text +
                "n\t**Error: You are not allowed to restore commands.**"
            )
    elif len(msg_list) == 1:
        yield from client.send_message(message.channel, help_text)
    else:
        yield from client.send_message(
            message.channel,
            help_text + "n\t**Error: Too many arguments.**")


@asyncio.coroutine
def command_important(message):
    help_text = """\
!commandimportant - Mod only, sets if a command is shown on the default\
!help menu
\t- Usage \"!commandimportant command_name [True | False]\""""
    msg_list = message.content.split(' ')
    if len(msg_list) == 3:
        if is_mod(message.author):
            if msg_list[2].lower() == "true"\
                    or msg_list[2].lower() == "false":
                command_name = msg_list[1]
                # Check if the command is in the list
                if command_name in config["Commands"]:
                    if msg_list[2].lower() == "true":
                        b = True
                    else:
                        b = False
                    config["Commands"][command_name]["Important"] = b
                    rewrite_config()
                    yield from client.send_message(
                        message.channel,
                        command_name + "'s importance set to " + b)
                else:
                    # Command not found
                    yield from client.send_message(
                        message.channel,
                        help_text + "n\t**Error: {0} not found.**"
                        .format(command_name))
            else:
                yield from client.send_message(
                    message.channel,
                    help_text +
                    "n\t**Error: Value must be true or false")
        else:
            yield from client.send_message(
                message.channel,
                help_text +
                "n\t**Error: You are not allowed to change commands.**")
    elif len(msg_list) == 1:
        yield from client.send_message(message.channel, help_text)
    else:
        yield from client.send_message(
            message.channel, help_text +
            "n\t**Error: Wrong number of arguments.**")


@asyncio.coroutine
def command_description(message):
    help_text = """\
!commanddesc - Mod only, changes the description of a command.
\t- Usage \"!commanddesc command_name Command Description\""""
    msg_list = message.content.split(' ')
    if len(msg_list) >= 3:
        if is_mod(message.author):
            command_name = msg_list[1]
            # Check if the command is in the list
            if command_name in config["Commands"]:
                # Command Found, time to set description
                desc = message.content.split(' ', 2)[2]
                config["Commands"][command_name]["Description"] = desc
                rewrite_config()
                yield from client.send_message(
                    message.channel,
                    command_name + "'s description set to: " + desc)
            else:
                # Command not found
                yield from client.send_message(
                    message.channel,
                    help_text +
                    "n\t**Error: {0} not found.**".format(command_name))
        else:
            yield from client.send_message(
                message.channel,
                help_text +
                "n\t**Error: You are not allowed to change commands.**")
    elif len(msg_list) == 1:
        yield from client.send_message(message.channel, help_text)
    else:
        yield from client.send_message(
            message.channel, help_text +
            "\n\t**Error: Wrong number of arguments.**")


def is_mod(user):
    super_users = config["Server Data"]["Mod Roles"]
    user_roles = []
    
    for role in user.roles:
        user_roles.append(role.name.lower())
    
    for role in super_users:
        lower_role = role.lower()
        if lower_role == "everyone":
            print("Granting access to {0} as everyone")
            return True
        if lower_role in user_roles:
            print("Granting access to {0} as role: {1}"
                  .format(user.id, lower_role))
            return True
    print("Returning false, {0} denied access. Bad roles: ")\
        .format(user.id)
    for role in user_roles:
        print("  " + role)
    return False


@asyncio.coroutine
def command_stream(message):
    streamers = config["Streamers"]
    help_text = """\
!stream - Usage \"!stream <streamer>\"

The added streamers are:"""   

    for streamer in streamers:
        help_text += "\n\t{0}".format(streamer)
    
    lis = message.content.split(' ')
    if len(lis) == 1:
        yield from client.send_message(message.channel, help_text)
        return
    
    streamer = lis[1].lower()
    
    for streamerKey in streamers:
        if streamer.startswith(streamerKey.lower()):
            reply = "{0} streams at {1}".format(streamerKey,
                                                streamers[streamerKey])
            yield from client.send_message(message.channel, reply)
            return
            
    print("Streamer not found: " + streamer)
    yield from client.send_message(
        message.channel, help_text +
        "\n\n\t**Error: Streamer not found**")
    return


@asyncio.coroutine
def command_source(message):
    reply = "{0}'s source code is available at " +\
            "http://github.com/mtvjr/WaifuBot"\
            .format(client.user.name)
    yield from client.send_message(message.channel, reply)


def gen_config():
    mod_roles = ["Admin", "Mod", "Moderator"]
    login_data = {"Email": "email@email.ext", "Password": "pAssw0rd"}
    server_data = {"Server Name": "Discord Server",
                   "Mod Roles": mod_roles,
                   "Server ID": "135531470562394112"}
    streamers = {"Joe": "Joe's Website", "Megan": "Megan's Website"}
    options_hi = ["Hello There!", "Howdy"]
    command_hi = {"Options": options_hi, "Description": "Says hello",
                  "Important": True}
    options_bye = ["Goodbye!"]
    command_bye = {"Options": options_bye,
                   "Description": "Says Goodbye", "Important": False}
    options_knock = ["Who's there?"]
    command_knock = {"Options": options_knock,
                     "Description": "Says Who's There?",
                     "Important": False}
    commands = {"hi": command_hi, "bye": command_bye}
    commands_deleted = {"Knock": command_knock}
    mentionable_users = [95704207738277888]
    global config
    config = {"Login Data": login_data, "Server Data": server_data,
              "Streamers": streamers, "Commands": commands,
              "Deleted Commands": commands_deleted,
              "Mentionable Users": mentionable_users}
    rewrite_config()
    return


def rewrite_config():
    f = open("config.yml", "w")
    yaml.dump(config, f, default_flow_style=False)


def set_name(name):
    if os.name == "nt":
        import ctypes
        ctypes.windll.kernel32.SetConsoleTitleA(str.encode(name))
    else:
        sys.stdout.write("\x1b]2;{0}\x07".format(name))


def safe_config_lookup(config_dict, key, default):
    if key not in config_dict:
        config_dict[key] = default
        rewrite_config()
    return config_dict[key]

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Check arguments
        if sys.argv[1] == "--generate-config":
            gen_config()
            exit()
    
    set_name("Waifu Bot")
    config = yaml.safe_load(open("config.yml"))
    loginData = config["Login Data"]
    client.run(loginData["Email"], loginData["Password"])
