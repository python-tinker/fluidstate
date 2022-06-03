import unittest

from fluidstate import InvalidTransition, StateMachine, state, transition


class MyMachine(StateMachine):

    initial_state = 'created'

    state('created')
    state('waiting')
    state('processed')
    state('canceled')

    transition(before='created', event='queue', after='waiting')
    transition(before='waiting', event='process', after='processed')
    transition(before=['waiting', 'created'], event='cancel', after='canceled')


class FluidstateEvent(unittest.TestCase):
    def test_its_declaration_creates_a_method_with_its_name(self):
        machine = MyMachine()
        assert hasattr(machine, 'queue') and callable(machine.queue)
        assert hasattr(machine, 'process') and callable(machine.process)

    def test_it_changes_machine_state(self):
        machine = MyMachine()
        machine.state == 'created'
        machine.queue()
        machine.state == 'waiting'
        machine.process()
        machine.state == 'processed'

    def test_it_ensures_event_order(self):
        machine = MyMachine()
        with self.assertRaises(InvalidTransition):
            machine.process()

        machine.queue()
        with self.assertRaises(InvalidTransition):
            machine.queue()
        try:
            machine.process
        except Exception:
            self.fail('machine process failed')

    def test_it_accepts_multiple_origin_states(self):
        machine = MyMachine()
        try:
            machine.cancel()
        except Exception:
            self.fail('cancel failed')

        machine = MyMachine()
        machine.queue()
        try:
            machine.cancel()
        except Exception:
            self.fail('cancel failed')

        machine = MyMachine()
        machine.queue()
        machine.process()
        with self.assertRaises(Exception):
            machine.cancel()


if __name__ == '__main__':
    unittest.main()
