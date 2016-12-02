from collections import defaultdict
import re
from threading import Thread

import chatexchange
from chatexchange import events

def get_subs(cls):
    subs = cls.__subclasses__()
    if subs:
        for sub in subs:
            yield from get_subs(sub)
    else:
        yield cls


def convert_cls_name(cls):
    return '_'.join([
        a.lower()
        for a in re.split('([A-Z][a-z]*)', cls.__name__)
            if a
    ])

class Events:
    events = {
        convert_cls_name(cls): cls.type_id for cls in get_subs(events.Event)
    }

    rooms = []

    @classmethod
    def register(cls, signal_name, event_cls):
        cls.events[signal_name.replace("-", "_")] = event_cls.type_id
        chatexchange.events.register_type(event_cls)
        for room in cls.rooms:
            room._events[event_cls.type_id] = defaultdict(dict)

    def __init__(self):
        raise Exception("Cannot instantiate class")


class Room(chatexchange.rooms.Room):
    def __init__(self, room_id, client):
        chatexchange.rooms.Room.__init__(self, room_id, client)
        Events.rooms.append(self)

        self._connection_id = 0
        self._ids = {}
        self._events = {}
        for type_id in Events.events.values():
            self._events[type_id] = defaultdict(dict)

        self.room_id = room_id
        self.join()
        self.watch_polling(lambda e,c: Thread(target=self.emit, args=(e,c)).start(), 1)


    def emit(self, event, client):
        events = self._events[event.type_id]
        for priority in sorted(events, reverse=True):
            for callback, args in events[priority].values():
                if callback(event, self, client, *args):
                    return


    def connect(self, event, callback, *args, priority=0):
        id = self._connection_id
        event = event.replace('-', '_')
        try:
            event_type = Events.events[event]
        except KeyError:
            raise ValueError("Unknown event: {!r}".format(event))

        self._events[Events.events[event]][priority][id] = (callback, args)
        self._ids[id] = (event, priority)
        self._connection_id += 1
        return id

    def disconnect(self, id):
        event, priority = self._ids.pop(id)
        self._events[Events.events[event]][priority].pop(id)



def quit(*a):
    for room in Events.rooms:
        room.leave()
