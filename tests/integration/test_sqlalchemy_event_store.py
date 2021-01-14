from datetime import datetime
import json
import logging
import uuid

import pytest
from application.adapters.orm import AggregateModel, EventModel
from application.adapters.event_store import SqlAlchemyEventStore
from application.domain.model import Application
from application.domain import events

pytestmark = pytest.mark.usefixtures('mappers')

logging.basicConfig(level=logging.DEBUG)
mylogger = logging.getLogger()


def initiate_application():
    id = uuid.uuid4()
    application = Application.initiate(
        aggregate_id=id,
        working_name='Working Name',
        cdwg_id='123456',
        ep_type="VCEP",
        initiation_date="2021-01-01"
    )
    return application

def test_can_load_an_event_stream(session_and_event_store_factory):
    session, event_store = session_and_event_store_factory()

    agg_id = uuid.uuid4()
    insert_aggregate(session, agg_id=agg_id)

    init_data = {
        "aggregate_id": str(id),
        "working_name": 'Working Name',
        "cdwg_id": '123456',
        "ep_type": "VCEP",
        "initiation_date": "2021-01-01"
    }

    insert_event(session, agg_id=agg_id, name='ApplicationInitiated', data=init_data)

    agg_stream = event_store.load_stream(aggregate_id=agg_id)

    assert len(agg_stream.events) == 1 
    assert isinstance(agg_stream.events[0], events.ApplicationInitiated)
    assert agg_stream.version == 1

    agg = Application(agg_stream.events, agg_stream.version)

    assert agg._version == 1
    assert len(agg._events) == 1

def test_stores_new_aggregate(session_and_event_store_factory):
    session, event_store = session_and_event_store_factory()
    application = initiate_application()
    
    event_store.store_changes(aggregate=application)
    session.commit()

    aggregates = session.query(AggregateModel).filter_by(id=str(application.id)).all()

    assert len(aggregates) == 1
    assert aggregates[0].version == 1
    assert aggregates[0].id == str(application.id)


def test_stores_events_in_the_database(session_and_event_store_factory):
    session, event_store = session_and_event_store_factory()

    application = initiate_application()
    event_store.store_changes(aggregate=application)
    session.commit()

    events = session.query(EventModel).filter_by(aggregate_id=str(application.id)).all()
    assert len(events) == 1

def test_appends_events_to_existing_aggregate_and_updates_version(session_and_event_store_factory):
    session, event_store = session_and_event_store_factory()
    application = initiate_application()
    event_store.store_changes(aggregate=application)
    session.commit()
    event_stream = event_store.load_stream(application.id)
    application = Application(event_stream.events, event_stream.version)

    application.add_contact(name='Elenor Shellstrop', email='elenor@medplace.com', phone="555-555-5555")
    application.add_contact(name='Chidi Anagonye', email='chidi@medplace.com', phone="555-555-5555")
    event_store.store_changes(aggregate=application)
    session.commit()

    aggregate = session.query(AggregateModel).filter_by(id=str(application.id)).one()
    assert aggregate.version == 2

    events = session.query(EventModel).filter_by(aggregate_id=str(application.id)).all()
    assert len(events) == 3

# helper methods

def insert_aggregate(session, agg_id:uuid.UUID, version:int=1):
    session.execute(
        'INSERT INTO aggregates (id, version) VALUES (:agg_id, :version)',
        dict(agg_id=str(agg_id), version=version)
    )

def insert_event(session, agg_id:uuid.UUID, name: str, data: dict, created_at:datetime=None):
    created_at = created_at if created_at else str(datetime.now())
    evt_id = uuid.uuid4()
    session.execute(
        'INSERT INTO events (id, aggregate_id, name, data, created_at) VALUES (:id, :agg_id, :name, :data, :created_at)',
        dict(id=str(evt_id), agg_id=str(agg_id), name=name, data=json.dumps(data), created_at=str(created_at))
    )

@pytest.fixture
def session_and_event_store_factory(sqlite_session_factory):
    def factory():
        session = sqlite_session_factory()
        event_store = SqlAlchemyEventStore(session)
        return session, event_store

    return factory