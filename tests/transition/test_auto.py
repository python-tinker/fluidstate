from fluidstate import StateChart, create_machine


class Machine(StateChart):
    create_machine(
        {
            'name': 'engine',
            'initial': 'engine',
            'states': [
                {'name': 'started'},
                {'name': 'stopped'},
            ],
            'transitions': [
                {
                    'event': '',
                    'target': 'started',
                },
            ],
        }
    )


def test_automatic_transition():
    machine = Machine()
    assert machine.initial == 'engine'
    assert machine.state == 'started'
