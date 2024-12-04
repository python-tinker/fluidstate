import pytest

from fluidstate import GuardNotSatisfied, StateChart


class FallingMachine(StateChart):
    __statechart__ = {
        'initial': 'looking',
        'states': [
            {
                'name': 'looking',
                'transitions': [
                    {
                        'event': 'jump',
                        'target': 'falling',
                        'cond': ['ready_to_fly', 'high_enough'],
                    }
                ],
            },
            {'name': 'falling'},
        ],
    }

    def __init__(self, ready=True):
        super().__init__()
        self.ready = ready
        self.high_enough_flag = True

    def ready_to_fly(self):
        return self.ready

    def high_enough(self):
        return self.high_enough_flag


def test_it_allows_transition_if_satisfied():
    machine = FallingMachine()
    machine.jump()
    assert machine.state == 'falling'


def test_it_forbids_transition_if_not_satisfied():
    machine = FallingMachine(ready=False)
    with pytest.raises(GuardNotSatisfied):
        machine.jump()


def test_it_may_be_an_attribute():
    """it may be an attribute, not only a method"""
    machine = FallingMachine()
    machine.ready_to_fly = False
    with pytest.raises(GuardNotSatisfied):
        machine.jump()

    machine.ready_to_fly = False
    with pytest.raises(Exception):
        machine.jump()
    assert machine.state != 'falling'


def test_it_allows_transition_only_if_all_are_satisfied():
    machine = FallingMachine()
    machine.ready_to_fly = True
    machine.high_enough_flag = True
    machine.jump()

    machine = FallingMachine()
    machine.ready_to_fly = False
    machine.high_enough_flag = True
    with pytest.raises(GuardNotSatisfied):
        machine.jump()

    machine = FallingMachine()
    machine.ready_to_fly = True
    machine.high_enough_flag = False
    with pytest.raises(GuardNotSatisfied):
        machine.jump()
