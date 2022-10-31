import pytest

from fluidstate import StateChart, State, Transition, states, transitions


class FallingMachine(StateChart):
    states(
        State(
            'looking',
            transitions(
                Transition(
                    event='jump',
                    target='falling',
                    cond=['ready_to_fly', 'high_enough'],
                )
            ),
        ),
        State('falling'),
    )
    initial = 'looking'

    def __init__(self, ready=True):
        super().__init__()
        self.ready = ready
        self.high_enough_flag = True

    def ready_to_fly(self):
        return self.ready

    def high_enough(self):
        return self.high_enough_flag


@pytest.fixture
def machine():
    f = FallingMachine()
    return f
