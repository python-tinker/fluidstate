"""Demonstrate iterating a statechart."""

from fluidstate import StateChart


class Nested(StateChart):
    """Proide an object representing a nested group of states."""

    __statechart__ = {
        'initial': 'start',
        'states': [
            {
                'name': 'start',
                'initial': 'inter1',
                'transitions': [
                    {
                        'event': 'change',
                        'target': 'start.inter1',
                    }
                ],
                'states': [
                    {
                        'name': 'inter1',
                        'transitions': [
                            {
                                'event': 'change',
                                'target': 'start.inter2',
                            }
                        ],
                    },
                    {
                        'name': 'inter2',
                        'initial': 'inter2_substate1',
                        'states': [
                            {
                                'name': 'inter2_substate1',
                                'transitions': [
                                    {'event': 'change', 'target': 'end'},
                                ],
                            },
                            {'name': 'inter2_substate2'},
                        ],
                        'transitions': [
                            {
                                'event': 'change',
                                'target': 'start.inter2.inter2_substate1',
                            }
                        ],
                    },
                ],
            },
            {'name': 'end'},
        ],
    }


def test_state_iteration_order() -> None:
    """Test state iteration order is breadth-first."""
    nested = Nested()
    assert [str(x) for x in nested.main] == [
        'State(main)',
        'State(start)',
        'State(end)',
        'State(inter1)',
        'State(inter2)',
        'State(inter2_substate1)',
        'State(inter2_substate2)',
    ]


def test_state_state_paths() -> None:
    """Test state contains path in tree."""
    nested = Nested()
    assert list(x.path for x in nested.main) == [
        'main',
        'main.start',
        'main.end',
        'main.start.inter1',
        'main.start.inter2',
        'main.start.inter2.inter2_substate1',
        'main.start.inter2.inter2_substate2',
    ]
