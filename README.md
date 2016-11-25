# Loquitor
A chatbot for Stack Exchange

##Installation and running

To install with pip, run:

    [sudo] pip3 install git+https://github.com/ralphembree/Loquitor.git --process-dependency-links

This will install the `loquitor` binary and the `Loquitor` Python package.

To run, just type `loquitor` (and ENTER) into a terminal.  You will be asked for an e-mail address, a password, the chat host (either stackoverflow.com, stackexchange.com, or meta.stackexchange.com), and the ID of the room you want to join.  After that is loaded and Loquitor has joined a room, the `translate` script will ask you for Bing translation credentials.  If you don't have any, just hit Enter to skip that feature.  Note that ignoring it instead of hitting Enter means that the rest of the scripts will not be run, so some commands might be missing.

You can also supply information as command-line options.  A full list of options can be seen by running `loquitor --help`.  Note that scripts such as `translate` are not run until after the command-line options are parsed, so they rely on environment variables if they can't have input.

Environment variables are also available for giving information.  The currently used ones are `LOQ_EMAIL`, `LOQ_PASSWORD`, `LOQ_SITE`, `BING_ID`, and `BING_SECRET`.  Using environment variables is helpful for when you would like to run loquitor in the background.  Just make sure that both `LOQ_EMAIL` and `LOQ_PASSWORD` are defined and that you run loquitor with the `--no-input` and `-r ROOM` options (`-r` gives the room ID).  If `--no-input` is given and `LOQ_SITE` is not defined, it will default to stackoverflow.com.  If `BING_ID` and/or `BING_SECRET` are not defined, the translate command will not be available.  If either of `LOQ_EMAIL` or `LOQ_PASSWORD` is not defined, loquitor will throw an error and return an exit code of 1.  Note that these behaviors are only if `--no-input` is given.

## Heroku

I run Loquitor on Heroku (but I hope to find something better).  I do that by connecting the Heroku account to [this Github repository](https://github.com/ralphembree/Loquitor-Heroku).  Details are given there.

## Commands

A command is given to the bot by prepending a chat message with `>>`.  Those commands are as follows:

* `define QUERY`: Searches wiktionary.org for the meaning of a word or phrase.
* `greet USER1 [USER2] [USER3] ...`: For each user given, greet that user (no @ is needed when giving the names.)
* `help [CMD]`: Gives help on all commands that implement help (probably everything).  If the name of a command is passed to `help` (without `>>`), it gives help on only that command.
* `kaomoji`: Displays a list of the kaomoji substitutions available.  If the `all` argument is given, it will also display the aliases.  The kaomoji substitutions occur when someone posts a message (without the >>) that matches one of Loquitor's substitution keys.  If it does, Loquitor will post a random kaomoji that matches that key.  For example, `&happy;` might give o((\*^▽^\*))o, (ﾉ^∇^)ﾉﾟ, ⌒°(ᴖ◡ᴖ)°⌒, or any of a dozen others.
* `meta QUERY`: Searches meta.stackoverflow.com and meta.stackexchange.com for QUERY.  It is a shortcut for `>>search site:(meta.stackoverflow.com or meta.stackexchange.com) QUERY`.
* `pause TIME`: Pauses for the specified amount of time.  When the bot is paused, it may respond to messages already posted, but it will not listen for more messages until the time runs out.  Only room owners can run this command.
* `say TEXT [to USER]`: Repeats text.  If `to USER` is given, prepends `@USER: ` to the message.  The ping happens only if `TEXT` is in quotation marks.  That is to prevent `>>say Go to England` from pinging the non-existent `England` user.
* `search QUERY`: Gives a list of ten search results from Bing.  Because of the limitations of chat formatting, the results are given like this:

>   \> Speedtest.net - Official Site, (https://speedtest.net)
>
   Test your Internet connection bandwidth to locations around the world with this interactive broadband speed test from Ookla 

* `test`: Responds with a random message taken from a list found [here](https://github.com/ralphembree/Loquitor/blob/master/bot.py#L24).
* `translate`: Translates a word or phrase. If multiple words are given, they should be surrounded with quotation marks.  The source language will be automatically detected, but it can be specified with `from LANG`.  The translated text will be in English unless `to LANG` is specified.
* `whatis`: Tries to find a definition of a word or phrase by searching Google for the phrase with `definition` prepended.  If Google's little custom response is not there, it resorts to the `define` command.
* `wiki`: Searches Wikipedia for a word or phrase.
* `wotd`: Finds the word of the day from Wiktionary.
* `xkcd`: Finds an xkcd comic given an ID or a search term.  Without arguments, gives a random comic.
* `youtube QUERY`: Searches YouTube for a video.  It responds with the first result one-boxed. The `yt` shortcut command can also be used.

## Contributing

Contributions are welcome.  Most of the background code should be done, so probably all that needs to be done is in the [scripts folder](scripts/). A file that is in the scripts folder will automatically be parsed for commands.  If a `main()` function is defined, it will be called when `bot.py` is run.  Otherwise, a `commands` dictionary will be looked for.  The two methods of adding commands are listed below.

### `main()` function

If a command file has a `main()` function, it will be executed, and it will be given these arguments:

    room: The `skeleton.Room` object that represents the room we are in.
    bot: The `bot.Bot` object connected to that room.
    client: The `stackexchange.client.Client` object that represents the account we are using.

The room is an object of type `skeleton.Room`, which is a subclass of `chatexchange.rooms.Room`.  The extra methods provided by `skeleton.Room` are as follows:

* `connect(signal, callback, priority=0)`: Registers a function to be called when a signal is emitted.  The optional priority sets some functions to be called before others (the higher priority is called first).  If a callback returns True, no other callbacks will be called.  The `connect()` method returns an ID that can be used for `disconnect()`.
* `disconnect(callback_id)`: Removes a function from the callback list.  The `callback_id` is the ID returned by `connect()`.
* `emit(event, client)`: Imitates an event.  Given an event and a client, it calls all the callbacks registered for that signal.  This is rarely used except in the background.

This is the only time the `bot` object is passed to a function.  The methods of a `Bot` are as follows:

* `get_help(command, args=())`: Gets help for a command.  If arguments are passed and the command's help is a function, the arguments will be passed to the function.
* `help_command(event, room, client)`: Propably doesn't need to be used.  This is the callback for the `>>help` command.
* `on_message(event, room, client)`: Probably doesn't need to be used.  This is the callback when any message is posted.
* `on_reply(event, room, client)`: Probably doesn't need to be used.  This is the callback when a bot's message is replied to.
* `register(command, function, help=None)`: To register a new command.  The command is passed as a string (without `>>`).  The function is called when that command is executed. (More information [below](#callbacks).)  The optional `help` argument is the string that will be used in the long help or in the help on that particular command.  It is planned to have two help texts
 for these two.  (More on that [below](#todo).)  A function could also be passed for help.  It will be called with whatever arguments are passed to the `help` command`.


### Commands dictionary

The `commands` dictionary is a mapping of commands to functions.  Each function should take three arguments: `room`, `event`, and `client.`  Here is an example:

    from random import choice

    YES_REPLIES = ("Yes.", "Oh, yeah!", "Uh huh.", "Definitely!", "Of course!", "Sure.")
    NO_REPLIES = ("I don't think so.", "No.", "No way!", "Certainly not!", "No, siree.")

    def say_yes_or_no(event, room, client):
        choices = choice([YES_REPLIES, NO_REPLIES])
        event.message.reply(choice(choices))
        
    commands = {
        'yes-or-no': say_yes_or_no, 'yes?': say_yes_or_no, 'no?': say_yes_or_no,
    }

More information about callbacks is given [below](#callbacks).  If a `help` dictionary is given, it can be used for command help:

    help = {
        'yes-or-no': 'Give a random response of yes or no.  yes? and no? are synonymous commands.',
    }

A function could also be used instead of a string.  Commands that do not appear in that `help` dictionary will not appear in the general help, and will reply with `Sorry, I can't help you with that.` if help is asked for that command.  Better help texts are planned [below](#todo).


### Callbacks

A callback is a function that is called when a signal is emitted.  A callback is given three arguments: `event`, `room`, and `client`.  The event is a subclass of `chatexchange.events.Event`. (Command events are subclasses of `bot.Command`).  The `bot.Command` events are just like `chatexchange.events.MessagePosted` events except that they have these three extra attributes (and keys of `event.data`): `command`, `query`, and `args`.  Here is an example:

    >>search Clark Gable "Gone with the Wind"

The event would be of type `Command_search`; `event.command` would be `search`; `event.query` would be `'Clark Gable "Gone with the Wind"'`; and `event.args` would be `['Clark', 'Gable', 'Gone with the Wind']`.  The most commonly-used attribute of an event is `event.message` because it provides `event.message.reply()`.

The `room` is a `skeleton.Room` object, which is a subclass of `chatexchange.rooms.Room`.  More information on that [above](#main-function)

The client is an instance of `chatexchange.client.Client`.


###Todo

#### bot.py

* Separate help texts for main and specific help commands.
* Option to have a different command prompt.
