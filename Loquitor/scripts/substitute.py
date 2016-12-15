from collections import defaultdict
import html
import os.path
import random
import sys
from warnings import warn


class main:
    PATH = os.path.join(os.path.expanduser("~"), ".loquitor", 'SUBSTITUTIONS.txt')
    VALUES = 0
    ALIAS = 1
    def __init__(self, room=None, bot=None, client=None, path=PATH):
        self.bot = bot
        self.subs = defaultdict(list)
        self.aliases = defaultdict(list)
        if path is not None:
            try:
                self.add(path)
            except IOError:
                warn("Could not open substitutions file.")
                try:
                    with open(path, 'w', encoding='utf-8'):
                        pass
                except IOError:
                    warn("Could not create substitutions file.")

        room.connect("message-posted", self.on_message_posted)
        bot.register("kaomoji", self.kaomoji_command, help="Display list of kaomojis supported.  With `kaomoji all`, even aliases will be displayed.")


    def add(self, path):
        key = None
        alias = None
        current = self.VALUES
        with open(path, encoding='utf-8') as infile:
            for line in infile:
                line = line.strip()
                if not line:
                    continue
                if line.lower().startswith("##define"):
                    new_key = line.partition(' ')[-1]
                    if new_key.strip():
                        key = new_key
                        alias = key
                        current = self.VALUES
                    else:
                        warn("Invalid key name: {}".format(new_key))
                elif line.lower().startswith("##alias"):
                    _, _, new_alias = line.partition(' ')
                    if new_alias.strip():
                        alias = new_alias
                    else:
                        alias = key
                    current = self.ALIAS
                elif current is self.VALUES:
                    self.subs[key].append(line)
                elif current is self.ALIAS:
                    self.aliases[line].append(alias)


    def get_keys(self, key):
        if key in self.subs:
            yield key
        if key in self.aliases:
            for key in self.aliases[key]:
                yield from self.get_keys(key)

    def get_random(self, key):
        choices = []
        for key in self.get_keys(key):
            choices += self.subs[key]

        return random.choice(choices)

    def kaomoji_command(self, event, room, client, bot):
        fmt = '{kaomoji}\n\nKamojis are triggered with an ampersand and a semicolon, but those punctuation characters are not generally needed.  Other than a semicolon, no punctuation can come after a kaomoji unless it is specifically set for that kaomoji.  For example, "huh?" and "what?" are valid, but "angry." is not.'

        args = event.args
        nargs = len(args)
        if nargs == 0:
            keys = self.subs.keys()
        elif (nargs == 1) and (args[0] == 'all'):
            keys = set(self.subs.keys()) | set(self.aliases.keys())
        else:
            event.content = " ".join(args)
            self.on_message_posted(event, room, client)
            return

        event.message.reply(fmt.format(kaomoji=" ".join(sorted(keys))), False)

    def on_message_posted(self, event, room, client):
        bot = sys.modules[self.bot.__module__]
        message = bot.remove_ctrl_chars(html.unescape(event.content))

        first_word = message.partition(' ')[0]
        used = set()
        lower_message = message.lower()
        words = message.split()
        lower_words = lower_message.split()
        word_keys = [" ".join(words[:i+1]) for i in range(len(words))]
        lower_word_keys = [" ".join(lower_words[:i+1]) for i in range(len(words))]
        keys = [message] + word_keys + [message.lower()] + lower_word_keys
        for key in keys:
            if key in used:
                continue
            try:
                room.send_message(self.get_random(key))
                break
            except IndexError:
                used.add(key)
