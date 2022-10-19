import unittest

from fluidstate import (
    InvalidTransition,
    StateChart,
    State,
    Transition,
    states,
)


class MyMachine(StateChart):

    initial = 'created'

    states(
        State(
            'created',
            transitions=[
                Transition(event='queue', target='waiting'),
                Transition(event='cancel', target='canceled'),
            ],
        ),
        State(
            'waiting',
            transitions=[
                Transition(event='process', target='processed'),
                Transition(event='cancel', target='canceled'),
            ],
        ),
        State('processed'),
        State('canceled'),
    )


class FluidstateEvent(unittest.TestCase):
    def test_its_declaration_creates_a_method_with_its_name(self):
        machine = MyMachine()
        assert hasattr(machine, 'queue') and callable(machine.queue)
        assert hasattr(machine, 'process') and callable(machine.process)

    def test_it_changes_machine_State(self):
        machine = MyMachine()
        machine.state == 'created'
        machine.queue()
        machine.state == 'waiting'
        machine.process()
        machine.state == 'processed'

    def test_it_ensures_event_order(self):
        machine = MyMachine()
        print(machine.state)
        with self.assertRaises(InvalidTransition):
            machine.process()

        machine.queue()
        with self.assertRaises(InvalidTransition):
            machine.queue()

        try:
            machine.process()
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
