from dataclasses import dataclass
from uuid import UUID

@dataclass(frozen=True)
class Event:
    aggregate_id: UUID

    def asdict(self):
        default_dict = self.__dict__
        default_dict['aggregate_id'] = str(self.aggregate_id)

        return default_dict


@dataclass(frozen=True)
class ApplicationInitiated(Event):
    working_name: str
    initiation_date: str
    ep_type: str
    cdwg_id: str

@dataclass(frozen=True)
class AddContact(Event):
    name: str
    email: str
    phone: str