# import pytest

from fluidstate import StateChart, State, Transition, create_machine


def test_it_defines_states():
    class MyMachine(StateChart):
        create_machine(
            {
                'initial': 'read',
                'states': [State('unread'), State('read'), State('closed')],
            }
        )

    machine = MyMachine()
    assert len(machine.states) == 3
    assert machine.states == ['unread', 'read', 'closed']


def test_it_has_an_initial():
    class MyMachine(StateChart):
        create_machine(
            {
                'initial': 'closed',
                'states': [State('open'), State('closed')],
            }
        )

    machine = MyMachine()
    assert machine.initial == 'closed'
    assert machine.state == 'closed'


def test_it_defines_states_using_method_calls():
    class MyMachine(StateChart):
        create_machine(
            {
                'initial': 'unread',
                'states': [
                    State(
                        'unread',
                        [Transition(event='read', target='read')],
                    ),
                    State(
                        'read',
                        [Transition(event='close', target='closed')],
                    ),
                    State('closed'),
                ],
            }
        )

    machine = MyMachine()
    assert len(machine.states) == 3
    assert machine.states == ['unread', 'read', 'closed']

    class OtherMachine(StateChart):
        create_machine(
            {
                'initial': 'idle',
                'states': [
                    State(
                        'idle',
                        [Transition(event='work', target='working')],
                    ),
                    State('working'),
                ],
            }
        )

    machine = OtherMachine()
    assert len(machine.states) == 2
    assert machine.states == ['idle', 'working']


# FIXME: cannot use lamda initialization
def test_its_initial_may_be_a_callable():
    def is_business_hours():
        return True

    class Person(StateChart):
        create_machine(
            {
                'initial': (
                    lambda person: (person.worker and is_business_hours())
                    and 'awake'
                    or 'sleeping'
                ),
                'states': [State('awake'), State('sleeping')],
            }
        )

        def __init__(self, worker):
            self.worker = worker
            super().__init__()

    person = Person(worker=True)
    assert person.state == 'awake'

    person = Person(worker=False)
    assert person.state == 'sleeping'
