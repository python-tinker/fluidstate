import unittest

from fluidstate import StateMachine, state, transition
from fluidstate import FluidstateInvalidTransition


class MyMachine(StateMachine):

    initial_state = 'created'

    state('created')
    state('waiting')
    state('processed')
    state('canceled')

    transition(source='created', event='queue', target='waiting')
    transition(source='waiting', event='process', target='processed')
    transition(
        source=['waiting', 'created'], event='cancel', target='canceled'
    )


class FluidityEvent(unittest.TestCase):
    def test_its_declaration_creates_a_method_with_its_name(self):
        machine = MyMachine()
        assert hasattr(machine, 'queue') and callable(machine.queue)
        assert hasattr(machine, 'process') and callable(machine.process)

    def test_it_changes_machine_state(self):
        machine = MyMachine()
        machine.current_state == 'created'
        machine.queue()
        machine.current_state == 'waiting'
        machine.process()
        machine.current_state == 'processed'

    def test_it_ensures_event_order(self):
        machine = MyMachine()
        with self.assertRaises(FluidstateInvalidTransition):
            machine.process()

        machine.queue()
        with self.assertRaises(FluidstateInvalidTransition):
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
