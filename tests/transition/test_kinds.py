# import pytest

from fluidstate import StateChart


class Machine(StateChart):
    __statechart__ = {
        'name': 'engine',
        'initial': 'engine',
        'states': [
            {
                'name': 'started',
                'transitions': [
                    # {'event': 'restart', 'target': 'started'},
                    {'event': 'stop', 'target': 'stopped'},
                ],
            },
            {'name': 'stopped'},
        ],
        'transitions': [
            {
                'event': '',
                'target': 'started',
            },
        ],
    }


machine = Machine()


def test_auto_transition():
    assert machine.initial == 'engine'
    assert machine.state == 'started'


# def test_self_transition():
#     machine.restart()
#     assert machine.state == 'started'


# def test_final_transition():
#     machine.stop()
#     assert machine.state.kind == 'final'
#     with pytest.raises(InvalidTransition):
#         machine.transition('started')
