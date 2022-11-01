import pytest

from fluidstate import (
    # InvalidTransition,
    StateChart,
    State,
    Transition,
    states,
)


class MyMachine(StateChart):
    initial = 'created'
    states(
        State(
            'created',
            transitions=[
                Transition(event='queue', target='waiting'),
                Transition(event='cancel', target='cancelled'),
            ],
        ),
        State(
            'waiting',
            transitions=[
                Transition(event='process', target='processed'),
                Transition(event='cancel', target='cancelled'),
            ],
        ),
        State('processed'),
        State('cancelled'),
    )


def test_its_declaration_creates_a_method_with_its_name():
    machine = MyMachine()
    assert hasattr(machine.state, 'queue') and callable(machine.state.queue)
    assert hasattr(machine.state, 'cancel') and callable(machine.state.cancel)
    machine.queue()


def test_it_changes_machine_State():
    machine = MyMachine()
    assert machine.state == 'created'
    machine.queue()
    assert machine.state == 'waiting'
    machine.process()
    assert machine.state == 'processed'


# XXX: invalid transition errors are local to state because of getattr
def test_it_ensures_event_order():
    machine = MyMachine()
    assert machine.state == 'created'
    with pytest.raises(AttributeError):
        machine.process()

    # with pytest.raises(InvalidTransition):

    machine.queue()
    assert machine.state == 'waiting'
    # waiting does not have queue transition
    with pytest.raises(AttributeError):
        machine.queue()

    # with pytest.raises(InvalidTransition):

    machine.process()
    assert machine.state == 'processed'
    # cannot cancel after processed
    with pytest.raises(Exception):
        machine.cancel()


def test_it_accepts_multiple_origin_states():
    machine = MyMachine(initial='processed')
    assert machine.state == 'processed'
    with pytest.raises(Exception):
        machine.cancel()

    machine = MyMachine(initial='cancelled')
    assert machine.state == 'cancelled'
    with pytest.raises(Exception):
        machine.queue()

    machine = MyMachine(initial='waiting')
    machine.process()
    assert machine.state == 'processed'
    with pytest.raises(Exception):
        machine.cancel()