import unittest
from fluidity import StateMachine, state, InvalidConfiguration


class FluidityConfigurationValidation(unittest.TestCase):
    def test_it_requires_at_least_two_states(self):
        class MyMachine(StateMachine):
            pass

        with self.assertRaises(InvalidConfiguration):
            MyMachine()
            # InvalidConfiguration, message="There must be at least two states"

        class OtherMachine(StateMachine):
            state('open')

        with self.assertRaises(InvalidConfiguration):
            OtherMachine()
            # InvalidConfiguration, message="There must be at least two states"

    def test_it_requires_an_initial_state(self):
        class MyMachine(StateMachine):
            state('open')
            state('closed')

        with self.assertRaises(InvalidConfiguration):
            MyMachine()
            # InvalidConfiguration, message="There must be at least two states"

        class AnotherMachine(StateMachine):
            state('open')
            state('closed')
            initial_state = None

        with self.assertRaises(InvalidConfiguration):
            AnotherMachine()
            # InvalidConfiguration, message="There must exist an initial state"


if __name__ == '__main__':
    unittest.main()
