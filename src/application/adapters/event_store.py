import abc
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Type, List
import uuid

from sqlalchemy.orm import Session, exc, joinedload
from sqlalchemy import update

import application.domain.events as eventsmodel
from application.domain.model import Aggregate
from application.domain import events
from .orm import AggregateModel, EventModel

class ConcurrentStreamWriteError(RuntimeError):
    pass

class NotFound(RuntimeError):
    pass

class EventStream:
    events: list[eventsmodel.Event]
    version: int

    def __init__(self, events: list[eventsmodel.Event], version: int):
        self.events = events
        self.version = version

class AbstractEventStore(metaclass=abc.ABCMeta):

    @abc.abstractmethod
    def load_stream(self, aggregate_id: uuid.UUID) -> EventStream:
        pass

    @abc.abstractmethod
    def store_changes(self, aggregate: Aggregate) -> None:
        pass

class SqlAlchemyEventStore(AbstractEventStore):
    def __init__(self, session: Session):
        self.session = session
    
    def load_stream(self, aggregate_id: uuid.UUID) -> eventsmodel.Event:
        try:
            aggregateResults: AggregateInstance = self.session.query(AggregateModel) \
                                                .options(joinedload('events')) \
                                                .filter(AggregateModel.id == str(aggregate_id)) \
                                                .one()            
        except exc.NoResultFound:
            raise NotFound('Could not find aggreagate with id '+str(aggregate.id))

        # return aggregateResults.events
        events_objects = [self._translate_to_object(model) for model in aggregateResults.events]
        version = aggregateResults.version
        return EventStream(events=events_objects, version=version)

    def store_changes(self, aggregate: Aggregate):
        if aggregate.version != 0:
            self._update_aggregate_version(aggregate=aggregate)
        else:
            self._create_new_aggregate(aggregate=aggregate)

        self._insert_events(
            aggregate=aggregate,
        )

    def _update_aggregate_version(self, aggregate: Aggregate):
        stmt = update(AggregateModel) \
                .values(version=aggregate.version+1) \
                .where(
                    (AggregateModel.version == aggregate.version)
                    & (AggregateModel.id == str(aggregate.id))
                )

        result_proxy = self.session.connection().execute(stmt)

        if result_proxy.rowcount != 1:
            raise ConcurrentStreamWriteError

    def _create_new_aggregate(self, aggregate: Aggregate):
        new_agg = AggregateModel(id=str(aggregate.id), version=1)
        self.session.add(new_agg)

    def _insert_events(self, aggregate: Aggregate):

        for event in aggregate.changes:
            new_event = EventModel(
                id=str(uuid.uuid4()),
                aggregate_id=str(aggregate.id),
                name=event.__class__.__name__,
                data=event.asdict(),
                created_at=datetime.now()
            )
            self.session.add(new_event)

    def _translate_to_object(self, event_model: eventsmodel.Event):
        class_name = event_model.name
        event_class: Type[events.Event] = getattr(events, class_name)

        return event_class(**event_model.data)
