import unittest
from fluidity import StateMachine, state, transition
from fluidity import InvalidTransition


class MyMachine(StateMachine):

    initial_state = 'off'

    state('off', before='inc_off')
    state('on', before='inc_on')

    transition(source='off', event='toggle', target='on')
    transition(source='on', event='toggle', target='off')

    def __init__(self):
        self.off_count = 0
        self.on_count = 0
        super(MyMachine, self).__init__()

    def inc_off(self):
        self.off_count += 1

    def inc_on(self):
        self.on_count += 1


class MachineIndependence(unittest.TestCase):
    def test_two_machines_dont_share_transitions(self):
        machine_a = MyMachine()
        machine_b = MyMachine()

        assert machine_a.current_state == 'off'
        assert machine_b.current_state == 'off'

        machine_a.toggle()

        assert machine_a.current_state == 'on'
        assert machine_b.current_state == 'off'

    def test_two_machines_dont_share_triggers(self):
        machine_a = MyMachine()
        machine_b = MyMachine()

        machine_a.on_count == 0
        machine_b.on_count == 0

        machine_a.toggle()

        machine_a.on_count == 1
        machine_b.on_count == 0
