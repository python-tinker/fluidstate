import unittest
from fluidstate import StateMachine, state, FluidstateInvalidConfig


class FluidstateConfigurationValidation(unittest.TestCase):
    def test_it_requires_at_least_two_states(self):
        class MyMachine(StateMachine):
            pass

        with self.assertRaises(FluidstateInvalidConfig):
            MyMachine()
            # FluidstateInvalidConfig, message="There must be at least two states"

        class OtherMachine(StateMachine):
            state('open')

        with self.assertRaises(FluidstateInvalidConfig):
            OtherMachine()
            # FluidstateInvalidConfig, message="There must be at least two states"

    def test_it_requires_an_initial_state(self):
        class MyMachine(StateMachine):
            state('open')
            state('closed')

        with self.assertRaises(FluidstateInvalidConfig):
            MyMachine()
            # FluidstateInvalidConfig, message="There must be at least two states"

        class AnotherMachine(StateMachine):
            state('open')
            state('closed')
            initial_state = None

        with self.assertRaises(FluidstateInvalidConfig):
            AnotherMachine()
            # FluidstateInvalidConfig, message="There must exist an initial state"


if __name__ == '__main__':
    unittest.main()
