import pytest

from fluidstate import (
    InvalidConfig,
    StateChart,
    State,
    states,
)


def test_it_requires_at_least_two_states():
    class MyMachine(StateChart):
        pass

    with pytest.raises(InvalidConfig):
        MyMachine()
        # InvalidConfig, message="There must be at least two states"

    class OtherMachine(StateChart):
        states(State('open'))

    with pytest.raises(InvalidConfig):
        OtherMachine()
        # InvalidConfig, message="There must be at least two states"


def test_it_requires_an_initial():
    class MyMachine(StateChart):
        states(State('open'), State('closed'))

    with pytest.raises(InvalidConfig):
        MyMachine()
        # InvalidConfig, message="There must be at least two states"

    class AnotherMachine(StateChart):
        states(State('open'), State('closed'))
        initial = None

    with pytest.raises(InvalidConfig):
        AnotherMachine()
        # InvalidConfig, message="There must exist an initial state"
