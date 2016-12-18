from random import choice
from re import findall
from string import punctuation

from urllib.request import urlopen
from bs4 import BeautifulSoup

from . import _parser

GREETINGS = (
    "Hey, {}. How are you?", "Hello, {}.", "Heyo there, {}!", "{}: Hello.",
    "Howdy, {}.",
)

INVALID_USER = [char for char in punctuation if char not in "'-"]

say_parser = _parser.Parser({'to': lambda t,a: a[0] if len(a) == 1 else False})

def convert_username(user_name, event=None):
    user_name = "".join([char for char in user_name if char not in INVALID_USER])
    if user_name == "me" and event is not None:
        return event.user_name
    return user_name

def on_say(event, room, client, bot):
    query = event.query
    if len(event.args) == 3 and event.args[1] == "to":
        user_name = convert_username(event.args[2], event)
        query = "@{}: {}".format(user_name, event.args[0])
    else:
        # \u200b is an invisible character to prevent recursion when the
        # query starts with the command prompt.
        query = "\u200b" + query.replace("@", "@\u200b")

    room.send_message(query)


def greet(room, user_name, event=None):
    user_name = convert_username(user_name, event)
    additional = "I am a bot. For a list of my commands, type `>>help`."
    greeting = " ".join([choice(GREETINGS), additional])
    room.send_message(greeting.format("@" + user_name))


def on_greet(event, room, client, bot):
    for user_name in event.args:
        # Assuming some non-programmer thinks it should be written in English.
        if user_name == "and":
            continue
        greet(room, user_name, event)

commands = {
    "greet": on_greet,
    "say": on_say,
}

help = {
    'greet': "Given a space-separated list of usernames, greet those users.",
    'say': "Repeat text. If `to USERNAME` is given, put @USERNAME: at the beginning of the message (messages directed to a user must be in quotation marks).",
}
