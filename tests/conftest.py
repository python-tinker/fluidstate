import pytest

from fluidstate import StateChart, State, Transition, states, transitions


class SwitchMachine(StateChart):

    initial = 'off'
    states(
        State(
            'off',
            transitions=[Transition(event='toggle', target='on')],
            on_entry='inc_off',
        ),
        State(
            'on',
            transitions=[Transition(event='toggle', target='off')],
            on_entry='inc_on',
        ),
    )

    def __init__(self):
        self.off_count = 0
        self.on_count = 0
        super().__init__()

    def inc_off(self):
        self.off_count += 1

    def inc_on(self):
        self.on_count += 1


@pytest.fixture
def switch_machine():
    machine = SwitchMachine()
    return machine


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
