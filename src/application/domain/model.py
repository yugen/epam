from dataclasses import dataclass
from functools import singledispatchmethod
import uuid

from . import events

class Aggregate:
    def __init__(self, events: list=None, version: int=None):
        self.id = None
        self._changes = [] # list of un-committed changes
        self._events = events or []
        self._version = version or 0

        self.replay()

    def replay(self):
        for e in self._events:
            self.apply(e)

    # Properties
    @property
    def changes(self):
        return self._changes

    @property
    def version(self):
        return self._version



class Application(Aggregate):

    def __init__(self, events: list=None, version: int=None):
        self._contacts = []
        super().__init__(events, version)

    # Deciders
    @classmethod
    def initiate(cls, *args, **kwargs):
        print(kwargs)
        event = events.ApplicationInitiated(**kwargs)
        instance = Application()
        instance.write_event(event)
        return instance

    def add_contact(self, name: str, email: str, phone: str):
        event = events.AddContact(aggregate_id=self.id, name=name, email=email, phone=phone)
        self.apply(event)
        self._changes.append(event)

    def write_event(self, event):
        self._events.append(event)
        self._changes.append(event)
        self.apply(event)

    # Appliers
    @singledispatchmethod
    def apply(self, arg):
        raise NotImplementedError('Can not apply event b/c single dispatch method not implemented.')

    @apply.register # ApplicationInitiated
    def _(self, event: events.ApplicationInitiated):
        self.id = event.aggregate_id
        self.working_name = event.working_name
        self.ep_type = event.ep_type
        self.cdwg_reference = event.cdwg_id
        self.initiation_date = event.initiation_date
    
    @apply.register # AddContact
    def _(self, event: events.AddContact):
        self._contacts.append(Contact(name=event.name, email=event.email, phone=event.phone))

    # helpers and properties

    @property
    def contacts(self):
        return self._contacts

 
@dataclass(frozen=True)
class Contact:
    name: str
    email: str
    phone: str

