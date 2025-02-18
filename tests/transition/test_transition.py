import pytest

from fluidstate import (
    InvalidTransition,
    StateChart
)


class MyMachine(StateChart):
    __statechart__ = {
        'initial': 'created',
        'states': [
            {
                'name': 'created',
                'transitions': [
                    {'event': 'queue', 'target': 'waiting'},
                    {'event': 'cancel', 'target': 'cancelled'},
                ],
            },
            {
                'name': 'waiting',
                'transitions': [
                    {'event': 'process', 'target': 'processed'},
                    {'event': 'cancel', 'target': 'cancelled'},
                ],
            },
            {'name': 'processed'},
            {'name': 'cancelled'},
        ],
    }


def test_it_changes_machine_state():
    machine = MyMachine()
    assert machine.state == 'created'
    machine.trigger('queue')
    assert machine.state == 'waiting'
    machine.trigger('process')
    assert machine.state == 'processed'


# XXX: invalid transition errors are local to state because of getattr
def test_it_ensures_event_order():
    machine = MyMachine()
    assert machine.state == 'created'
    with pytest.raises(InvalidTransition):
        machine.trigger('process')

    # with pytest.raises(InvalidTransition):

    machine.trigger('queue')
    assert machine.state == 'waiting'
    # waiting does not have queue transition
    with pytest.raises(InvalidTransition):
        machine.trigger('queue')

    # with pytest.raises(InvalidTransition):

    machine.trigger('process')
    assert machine.state == 'processed'
    # cannot cancel after processed
    with pytest.raises(Exception):
        machine.trigger('cancel')


def test_it_accepts_multiple_origin_states():
    machine = MyMachine(initial='processed')
    assert machine.state == 'processed'
    with pytest.raises(Exception):
        machine.trigger('cancel')

    machine = MyMachine(initial='cancelled')
    assert machine.state == 'cancelled'
    with pytest.raises(Exception):
        machine.trigger('queue')

    machine = MyMachine(initial='waiting')
    machine.trigger('process')
    assert machine.state == 'processed'
    with pytest.raises(Exception):
        machine.trigger('cancel')
