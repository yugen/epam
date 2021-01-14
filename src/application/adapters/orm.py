from dataclasses import dataclass
import logging
from sqlalchemy import (
    Table, MetaData, Column, Integer, String, Date, ForeignKey,
    event, JSON, DateTime
)
from sqlalchemy.orm import mapper, relationship

from application.domain import model
# from application.domain import events as eventmodels

# logger = logging.getLogger(__name__)

metadata = MetaData()

aggregates = Table(
    'aggregates', metadata,
    Column('id', String(36), primary_key=True),
    Column('version', Integer, nullable=False, server_default='1'),
)


events = Table(
    'events', metadata,
    Column('id', String(36), primary_key=True),
    Column('name', String(50)),
    Column('aggregate_id', ForeignKey('aggregates.id')),
    Column('data', JSON),
    Column('created_at', DateTime)
)

@dataclass
class EventModel():
    id: str
    name: str
    aggregate_id: str
    data: str
    created_at: str

@dataclass
class AggregateModel():
    id: str
    version: int
    # events: list

def start_mappers():
    # logger.info("Starting mappers")

    events_mapper = mapper(EventModel, events)
    aggregates_mapper = mapper(AggregateModel, aggregates, properties={
                                'events': relationship(EventModel)
                            })
# @event.listens_for(model.Product, 'load')
# def receive_load(product, _):
#     product.events = []


