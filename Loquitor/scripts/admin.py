import html
import sys
import time

from chatexchange.messages import Message
from requests.exceptions import HTTPError

exponents = {
    'yactosecond': -24,
    'zeptosecond': -21,
    'attosecond': -18,
    'femtosecond': -15,
    'svedberg': -13,
    'picosecond': -12,
    'nanosecond': -9,
    'shake': -8,
    'microsecond': -6,
    'millisecond': -3,
    'second': 0,
    'kilosecond': 3,
    'megasecond': 6,
    'gigasecond': 9,
    'terasecond': 12,
}

fractions = {
    'minute': 60,
    'moment': 90,
    'ke': 864,
    'hour': 3600,
    'day': 86400,
    'week': 604800,
    'fortnight': 1209600,
    'month': 2592000,
    'year': 31536000,
    'lustrum': 157680000,
    'decade': 315360000,
    'indiction': 473040000,
    'jubilee': 1576800000,
    'century': 3153600000,
    'millenium': 3153600000,
    'kiloannum': 3153600000,
}

def human_to_seconds(string):
    total = 0
    for part in string.split(','):
        try:
            number, unit = part.split()
            number = int(number)
        except ValueError:
            raise ValueError("Invalid time: {!r}".format(part))
        if unit.endswith("s"):
            unit = unit[:-1]
        if unit in fractions:
            total += number * fractions[unit]
        elif unit in exponents:
            total += number * (10 ** exponents[unit])
        else:
            raise ValueError("Unknown time unit: {!r}".format(unit))
    return total

class Delete:
    def __init__(self, room, bot, client):
        bot_module = sys.modules[bot.__module__]
        self.get_query_args = getattr(bot_module, 'get_query_args')
        room.connect("message-reply", self.on_reply)
        bot.register("delete", self.delete_command, help="Syntax: delete <id> <id2> <id3> ...  Deletes own messages, specified by IDs. The reply syntax can also be used.  Just reply to a message with the single word `delete`, and the bot will try to delete it.")

    def on_command(self, event, room, client, bot):
        bot.register_response(event.data['message_id'], self.delete_reply)

    def on_reply(self, event, room, client):
        _, _, string = html.unescape(event.content).partition(' ')
        command = string.split()[0]
        if command == "delete":
            message = client.get_message(event.data['message_id']).parent
            message_id = message.id
            event.data['command'] = 'delete'
            event.data['query'] = str(message_id)
            event.data['message_id'] = message_id
            event.data['args'] = [str(message_id)]
            for key in ('command', 'query', 'message_id', 'args'):
                setattr(event, key, event.data[key])
            self.delete_command(event, room, client)

    def delete_command(self, event, room, client, bot=None):
        args = event.args
        messages = []
        if args:
            for arg in args:
                try:
                    message = client.get_message(int(arg))
                    owner = message.owner
                    if owner == client.get_me():
                        message.delete()
                    else:
                        messages.append("{} is not one of my messages.".format(arg))
                except ValueError:
                    messages.append("{} is not a valid integer.".format(arg))
                except HTTPError:
                    messages.append("No message with {} id exists.".format(arg))
            if messages:
                if bot is not None:
                    messages.insert(0, "Some of the messages were not deleted.")
                message = "\n".join(messages)
                event.message.reply(message, False)
        else:
            event.message.reply("To delete a message, reply to that message with the word `delete` or give me an id.")


class Pause:
    def __init__(self, room, bot, client):
        self.play_time = 0
        bot.register("pause", self.pause, help="Given `>>pause 4 minutes`, stop listening for commands for 4 minutes.  Many time units are supported.  This is a RO-only command.")
        room.connect("message-posted", self.message_posted, priority=1)

    def message_posted(self, event, room, client):
        return time.time() <= self.play_time

    def pause(self, event, room, client, bot):
        if event.data['user_id'] not in (user.id for user in event.room.owners):
            event.message.reply("Only room owners have permission to run this command.")
            return
        try:
            length = round(human_to_seconds(event.query), 3)
        except ValueError:
            event.message.reply("I don't understand how long that is.")
        else:
            self.play_time = time.time() + length
            bot.register_response(event.data['message_id'], self.on_reply)
            event.message.reply("I am pausing for {}. Reply `cancel` if you would like to undo.".format(event.query))

    def on_reply(self, event, room, client):
        if (self.play_time == 0) or (time.time() > self.play_time):
            event.message.reply("I'm already in action.")
            return
        if event.query == "cancel":
            if event.data['user_id'] in (user.id for user in event.room.owners):
                self.play_time = 0
                room.send_message("I am back in action.")
            else:
                event.message.reply("Only room owners can cancel.")
        else:
            event.message.reply("Only `cancel` is recognized.")

def main(room, bot, client):
    pause = Pause(room, bot, client)
    delete = Delete(room, bot, client)
