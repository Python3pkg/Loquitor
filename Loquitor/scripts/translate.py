from getpass import getpass
import locale
import os

from BingTranslator import Translator

from . import _parser

class UnknownLanguageError(_parser.ParsingError):
    def __init__(self, language):
        _parser.ParsingError.__init__(self, language)
        self.language = language


class main:
    def __init__(self, room, bot, client):
        if bot.no_input:
            client_id = os.getenv("BING_ID")
            secret = os.getenv("BING_SECRET")
            if None in (client_id, secret):
                return
        else:
            print("If you would like to have the translate command, please give your Bing translation credentials.  If you aren't willing, just hit Enter to skip this feature.")
            client_id = input("Client ID: ")
            if not client_id:
                return
            secret = getpass("Secret: ")
            if not secret:
                return

        self.translator = Translator(client_id, secret)
        self.parser = _parser.Parser(['from', 'to'], self.parse_token)
        bot.register("translate", self.on_translate, help="Translate word/phrase using Bing's translation API.  By default, the source language is guessed, and the target language is English, but you can specify with the `from` and `to` keywords (at the end of the command).  Multi-word texts should be in quotation marks.")

    def parse_token(self, token, args):
        num_args = len(args)
        if num_args == 0:
            raise UnknownLanguageError("")
        elif num_args == 1:
            try:
                return self.normalize(args[0])
            except ValueError:
                raise UnknownLanguageError("")
        else:
            try:
                return self.normalize(" ".join(args))
            except ValueError:
                return False

    def on_translate(self, event, room, client, bot):
        words = event.args
        keys = {'from': 'from_lang', 'to': 'to_lang'}
        dic = {keys['to']: 'en'}
        try:
            parsed = self.parser.parse(words)
            leftover = parsed.pop('leftover')
            if len(leftover) > 1:
                event.message.reply("Either you didn't put your text in quotation marks, or you're trying to use commands that I don't understand.")
            else:
                text = " ".join(leftover)
                for key, value in parsed.items():
                    dic[keys[key]] = value
                event.message.reply(self.translator.translate(text, **dic), False)
        except UnknownLanguageError as e:
            event.message.reply("I don't understand what {!r} is.".format(e.language))


    def normalize(self, lang):
        # Normalized good locale codes will strip the spaces, but bad ones
        # remain as is.
        normalized = locale.normalize(lang)
        if normalized == lang and locale.normalize(lang + ' ') == lang + ' ':
            lang = lang.strip()
            raise ValueError("Unknown locale code: {}".format(lang), lang)
        return normalized[:2]

