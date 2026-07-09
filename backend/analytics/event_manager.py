from collections import deque

class EventManager:

    def __init__(self):
        self.events = deque(maxlen=200)

    def add_events(self, events):

        for event in events:
            self.events.appendleft(event)

    def get_events(self):
        return list(self.events)