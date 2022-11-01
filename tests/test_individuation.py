"""Fluidstate object (individuation)"""

# import pytest

from fluidstate import StateChart, State, Transition, states


class Door(StateChart):
    states(
        State(
            'closed',
            [Transition(event='open', target='opened')],
        ),
        State('opened'),
    )
    initial = 'closed'


door = Door()
door.add_state(State('broken'))
door.add_transition(
    Transition(event='crack', target='broken'),
    state='closed',
)


def test_it_responds_to_an_event():
    assert hasattr(door, 'crack')


def test_event_changes_state_when_called():
    door.crack()
    assert door.state == 'broken'


def test_it_informs_all_its_states():
    assert len(door.states) == 3
    assert door.states == ['closed', 'opened', 'broken']


# XXX: this has been converted to __getattr__ instead
# def test_individuation_does_not_affect_other_instances():
#     another_door = Door()
#     assert not hasattr(another_door.state, 'crack')
