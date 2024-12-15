import pytest

from fluidstate import InvalidConfig, StateChart, State


def test_it_requires_at_least_root_state() -> None:
    class Machine(StateChart):
        """Example machine without a root state."""

    # There must be a root state
    with pytest.raises(InvalidConfig):
        Machine()


def test_it_requires_at_least_two_states() -> None:
    with pytest.raises(InvalidConfig):

        class Machine(StateChart):
            """Example compound state missing minimal substates."""

            __statechart__ = {'states': [State('open')]}


def test_it_requires_an_initial():
    class Machine(StateChart):
        __statechart__ = {'states': [State('open'), State('closed')]}

    machine = Machine()
    assert machine.state == 'open'


def test_initial_state_default() -> None:
    class Machine(StateChart):
        __statechart__ = {
            'initial': None,
            'states': [State('open'), State('closed')],
        }

    # An initial state must exist.
    machine = Machine()
    assert machine.state == 'open'
