#!/usr/bin/env python

from code import interact
import csv
from getpass import getpass
import html
from random import choice
import shlex
import sys
from traceback import print_exc

import chatexchange

import skeleton

class Bot:
    UNKNOWN_MESSAGES = (
        "I don't know what that means.", "Sorry, I don't understand.",
        "Huh?", "What does that mean?", "That isn't in my dictionary.",
        "I don't get what you're trying to say.", "I don't get it.",
        "That doesn't make any sense",
    )
    TEST_MESSAGES = (
        "This is just a test.", "I'm working.", "Hey.",
        "Test yourself, and see how you like it.", "Don't bother me.",
        "https://i.stack.imgur.com/N64oS.gif", "I'm too tired to respond.",
        "Today's my day off.  Can't it wait?", "When do I get a vacation?",
        "Maybe later, okay?", "Leave me alone.", "What do you want?",
    )
    NUEL_TESTS = (
        "https://chat.stackoverflow.com/transcript/85048?m=33126572#33126572",
        "https://chat.stackoverflow.com/transcript/85048?m=33101025#33101025",
        "https://chat.stackoverflow.com/transcript/85048?m=32915719#32915719",
        "https://chat.stackoverflow.com/transcript/85048?m=32807076#32807076",
        "https://chat.stackoverflow.com/transcript/85048?m=32774161#32774161",
        "https://chat.stackoverflow.com/transcript/85048?m=33149227#33149227",
        "https://chat.stackoverflow.com/transcript/85048?m=32926859#32926859",
        "https://chat.stackoverflow.com/transcript/85048?m=33083381#33083381",
        "https://chat.stackoverflow.com/transcript/85048?m=33083372#33083372",
        "https://chat.stackoverflow.com/transcript/85048?m=33083371#33083371",
        "https://chat.stackoverflow.com/transcript/85048?m=33083332#33083332",
        "https://chat.stackoverflow.com/transcript/85048?m=33079296#33079296",
        "https://chat.stackoverflow.com/transcript/85048?m=33068126#33068126",
        "https://chat.stackoverflow.com/transcript/85048?m=32828808#32828808",
        "https://chat.stackoverflow.com/transcript/85048?m=32774149#32774149",
    )
    def __init__(self, room, client):
        if not client.logged_in:
            raise ValueError("Client must be logged in.")

        self.room = room
        self.client = client

        self.commands = {}

        self.register("test", self.test_command, help="It didn't work.")
        self.register("help", self.help_command, help="Syntax: `help` or `help <cmd>`.  If cmd supports arguments, `help <cmd> <cmd-args>` may be possible")
        self.room.connect('message-posted', self.on_message)

    def test_command(self, event, room, client):
        """Registering this command was as simple as:

        bot.register("test", test_command)"""

        if event.data['user_id'] == 5768335:
            message = choice(self.NUEL_TESTS)
        else:
            message = choice(self.TEST_MESSAGES)
        event.respond(message)

    def get_help(self, command, args=()):
        if command not in self.commands:
            return None

        command_help = self.commands[command].help
        if callable(command_help):
            return command_help(*args)
        return command_help
            

    def help_command(self, event, room, client):
        args = event.args

        if args:
            cmd = args[0]
            cmd_args = args[1:]
            help = "*{}*: {}".format(cmd, self.get_help(cmd, cmd_args))
            if help is None:
                help = "Sorry, I can't help you with that."
            event.respond(help)

        else:
            helps = []
            for command in self.commands:
                help = self.get_help(command)
                if help is not None:
                    helps.append(">>{}: {}".format(command, help))

            message = "\n".join(helps)
            message += "\n\nMy commands always start with >>.  For example, >>test is a command that will respond to you with some random messages.  Try `help <cmd>` for help on the other commands."

            event.respond(message, False)
            return message


    def register(self, command, function, help=None):
        signal_name = 'Command_{}'.format(command)
        event_cls = type(signal_name, (Command,), {})
        event_cls.help = help
        skeleton.Events.register(signal_name, event_cls)
        self.commands[command] = event_cls
        self.room.connect(signal_name, function)

    def on_message(self, event, room, client):
        message = html.unescape(event.content)
        if message.startswith(">>"):
            message = message[2:]
            # Puts quoted text as one argument, but ignores apostrophes
            command, _, query = message.partition(' ')
            query = query.strip()
            args = next(csv.reader([query], delimiter=" "))
            event.data['command'] = command
            event.data['query'] = query
            event.data['args'] = args
            event.data['respond'] = lambda string, len_check=False:\
                room.send_message(
                    ":{} {}".format(event.data['message_id'], string),
                    len_check
                )

            if command in self.commands:
                event.data['event_type'] = 'Command_{}'.format(command)
                new_event = self.commands[command](event.data, client)
                try:
                    room.emit(new_event, client)
                except Exception as e:
                    new_event.respond("Oops. That's an error: {}".format(e))
                    print_exc()

            else:
                message = choice(self.UNKNOWN_MESSAGES)
                event.data['respond'](message)

        

class EventMeta(type, chatexchange.events.Event):
    def __new__(self, class_name, bases, attrs):
        attrs['type_id'] = class_name
        if '__init__' not in attrs:
            attrs['__init__'] = self._default_init

        event_vars = dict(vars(chatexchange.events.Event))
        del event_vars['__init__']
        attrs.update(event_vars)

        return type.__new__(self, class_name, bases, attrs)

    def _default_init(self, data, client):
        chatexchange.events.Event.__init__(self, data, client)
        for key, value in data.items():
            setattr(self, key, value)

class Command(metaclass=EventMeta):
    pass

skeleton.Events.register('command', Command)


def main(room, username, password, host='stackoverflow.com'):
    import scripts

    client = chatexchange.Client(host, username, password)
    room = skeleton.Room(room, client)
    bot = Bot(room, client)

    for module_name in scripts.__all__:
        module = sys.modules['scripts.{}'.format(module_name)]
        if hasattr(module, 'main') and callable(module.main):
            module.main(room, bot, client)
        elif hasattr(module, 'commands') and hasattr(module.commands, 'items'):
            for com_name, func in module.commands.items():
                bot.register(com_name, func)

            if hasattr(module, 'help') and hasattr(module.help, 'items'):
                for command, help in module.help.items():
                    bot.commands[command].help = help
        else:
            print("Invalid script file: {!r}".format(module_name))


    interact(banner="Welcome to Loquitor!", local=locals())


if __name__ == '__main__':
    username = input("E-mail: ")
    password = getpass("Password: ")
    room = input("What room would you like to join? ")
    while True:
        try:
            room = int(room)
            break
        except ValueError:
            room = input("Please type an integer: ")

    print("Loading...", end='\r')
    main(1, username, password)