#!/usr/bin/env python

from code import interact
import csv
from getpass import getpass
import html
from random import choice
import shlex
import sys
import time
from traceback import print_exc
import unicodedata

import chatexchange

from . import skeleton

class Bot:
    UNKNOWN_MESSAGES = (
        "I don't know what that means.", "Sorry, I don't understand.",
        "Huh?", "What does that mean?", "That isn't in my dictionary.",
        "I don't get what you're trying to say.", "I don't get it.",
        "That doesn't make any sense", "what you mean?",
    )
    TEST_MESSAGES = (
        "This is just a test.", "I'm working.", "Hey.",
        "Test yourself, and see how you like it.", "Don't bother me.",
        "https://i.stack.imgur.com/N64oS.gif", "I'm too tired to respond.",
        "Today's my day off.  Can't it wait?", "When do I get a vacation?",
        "Maybe later, okay?", "Leave me alone.", "What do you want?",
    )
    NUEL_TESTS = (
        "https://chat.stackoverflow.com/transcript/message/33352696",
        "https://chat.stackoverflow.com/transcript/message/33126572",
        "https://chat.stackoverflow.com/transcript/message/33101025",
        "https://chat.stackoverflow.com/transcript/message/32915719",
        "https://chat.stackoverflow.com/transcript/message/32807076",
        "https://chat.stackoverflow.com/transcript/message/32774161",
        "https://chat.stackoverflow.com/transcript/message/33149227",
        "https://chat.stackoverflow.com/transcript/message/32926859",
        "https://chat.stackoverflow.com/transcript/message/33083381",
        "https://chat.stackoverflow.com/transcript/message/33083372",
        "https://chat.stackoverflow.com/transcript/message/33083371",
        "https://chat.stackoverflow.com/transcript/message/33083332",
        "https://chat.stackoverflow.com/transcript/message/33079296",
        "https://chat.stackoverflow.com/transcript/message/33068126",
        "https://chat.stackoverflow.com/transcript/message/32828808",
        "https://chat.stackoverflow.com/transcript/message/32774149",
        "https://chat.stackoverflow.com/transcript/message/33205426",
        "https://chat.stackoverflow.com/transcript/message/33205433",
        "https://chat.stackoverflow.com/transcript/message/33205448",
        "https://chat.stackoverflow.com/transcript/message/33205451",

    )
    def __init__(self, room, client, config_dir, no_input):
        if not client.logged_in:
            raise ValueError("Client must be logged in.")

        self.room = room
        self.client = client
        self.config_dir = config_dir
        self.no_input = no_input

        self.commands = {}
        self.responses = {}

        self.register("test", self.test_command, help="It didn't work.")
        self.register("help", self.help_command, help="Syntax: `help` or `help <cmd>`.  If cmd supports arguments, `help <cmd> <cmd-args>` may be possible")
        self.room.connect('message-posted', self.on_message)
        self.room.connect('message-reply', self.on_reply)

    def test_command(self, event, room, client, bot):
        """Registering this command was as simple as:

        bot.register("test", test_command)"""

        if event.data['user_id'] == 5768335:
            response = choice(self.NUEL_TESTS)
        else:
            response = choice(self.TEST_MESSAGES)
        event.message.reply(response)

    def get_help(self, command, args=()):
        if command not in self.commands:
            return None

        command_help = self.commands[command].help
        if callable(command_help):
            return command_help(*args)
        return command_help
            

    def help_command(self, event, room, client, bot):
        args = event.args

        if args:
            cmd = args[0]
            cmd_args = args[1:]
            help = "*{}*: {}".format(cmd, bot.get_help(cmd, cmd_args))
            if help is None:
                help = "Sorry, I can't help you with that."
            event.message.reply(help)

        else:
            helps = []
            for command in sorted(bot.commands):
                help = bot.get_help(command)
                if help is not None:
                    helps.append(">>{}: {}".format(command, help))

            message = "\n".join(helps)
            message += "\n\nMy commands always start with >>.  For example, >>test is a command that will respond to you with some random messages.  Try `help <cmd>` for help on the other commands."

            event.message.reply(message, False)
            return message


    def register(self, command, function, help=None):
        signal_name = 'Command_{}'.format(command)
        event_cls = type(signal_name, (Command,), {})
        event_cls.help = help
        try:
            skeleton.Events.register(signal_name, event_cls)
        except AssertionError: # If a bot was run before
            pass
        self.commands[command] = event_cls
        self.room.connect(signal_name, function, self)

    def register_response(self, message_id, function):
        self.responses[message_id] = function

    def register_responses(self, *args):
        for message_id, function in args:
            self.register_response(message_id, function)

    def on_reply(self, event, room, client):
        response_id = event.message.parent._parent_message_id
        if response_id in self.responses:
            message = event.message.content.partition(' ')[-1]
            query, args = get_query_args(message)
            event.data['query'] = query
            event.data['args'] = args
            event.data.update(vars(event))
            for key, value in event.data.items():
                setattr(event, key, value)
            self.responses[response_id](event, room, client)

    def on_message(self, event, room, client):
        message = html.unescape(event.content)
        if message.startswith(">>"):
            message = message[2:].strip()
            command, _, query = message.partition(' ')
            query, args = get_query_args(query)
            event.data['command'] = command
            event.data['query'] = query
            event.data['args'] = args
            event.data.update(vars(event))
            if command in self.commands:
                event.data['event_type'] = 'Command'
                first_event = Command(event.data, client)
                event.data['event_type'] = 'Command_{}'.format(command)
                new_event = self.commands[command](event.data, client)
                try:
                    if not room.emit(first_event, client):
                        room.emit(new_event, client)
                except Exception as e:
                    new_event.message.reply("Oops. That's an error: {}".format(e))
                    print_exc()

            else:
                message = choice(self.UNKNOWN_MESSAGES)
                event.message.reply(message)

        

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

skeleton.Events.register('Command', Command)


def main(username, password, room, config_dir, host='stackoverflow.com', no_input=False):
    from . import scripts

    client = chatexchange.Client(host, username, password)
    room = skeleton.Room(room, client)
    bot = Bot(room, client, config_dir, no_input)

    for module_name in scripts.__all__:
        module = sys.modules['Loquitor.scripts.{}'.format(module_name)]
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

    return client, room, bot


def remove_ctrl_chars(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

def get_query_args(string):
    query = remove_ctrl_chars(string).strip()
    args = next(csv.reader([query], delimiter=" "))
    return query, args
