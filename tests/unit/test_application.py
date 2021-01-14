import uuid

from application.domain.model import Application, Contact
import application.domain.events as events

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

def test_initiating_new_Application_adds_ApplicationInitiated_to_event_stream():
    application = initiate_application()

    assert len(application._changes) == 1
    assert isinstance(application._changes[0], events.ApplicationInitiated)

def test_applies_initial_attribues_when_initiated():
    application = initiate_application()

    assert application.working_name == 'Working Name'
    assert application.cdwg_reference == '123456'
    assert application.ep_type == 'VCEP'
    assert application.initiation_date == '2021-01-01'

def test_can_add_a_contact_to_an_application():
    application = initiate_application()

    contact_info = {'name': "Jason Mendoza", 'email': "bortlesfan@jacksonville.net", 'phone': "555-555-5555"}
    application.add_contact(**contact_info)

    assert len(application._changes) == 2
    assert len(application._contacts) == 1
    assert application._contacts[0] == Contact(**contact_info)
