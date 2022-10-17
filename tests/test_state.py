import unittest

from fluidstate import StateChart, state, transition


class FluidstateState(unittest.TestCase):
    def test_it_defines_states(self):
        class MyMachine(StateChart):
            state('unread')
            state('read')
            state('closed')
            initial_state = 'read'

        machine = MyMachine()
        assert len(machine.states) == 3
        assert machine.states == ['unread', 'read', 'closed']

    def test_it_has_an_initial_state(self):
        class MyMachine(StateChart):
            initial_state = 'closed'
            state('open')
            state('closed')

        machine = MyMachine()
        assert machine.initial_state == 'closed'
        assert machine.state == 'closed'

    def test_it_defines_states_using_method_calls(self):
        class MyMachine(StateChart):
            state('unread')
            state('read')
            state('closed')
            initial_state = 'unread'
            transition(event='read', target='read')
            transition(event='close', target='closed')

        machine = MyMachine()
        assert len(machine.states) == 3
        assert machine.states == ['unread', 'read', 'closed']

        class OtherMachine(StateChart):
            state('idle')
            state('working')
            initial_state = 'idle'
            transition(event='work', target='working')

        machine = OtherMachine()
        assert len(machine.states) == 2
        assert machine.states == ['idle', 'working']

    def test_its_initial_state_may_be_a_callable(self):
        def is_business_hours():
            return True

        class Person(StateChart):
            initial_state = (
                lambda person: (person.worker and is_business_hours())
                and 'awake'
                or 'sleeping'
            )
            state('awake')
            state('sleeping')

            def __init__(self, worker):
                self.worker = worker
                StateChart.__init__(self)

        person = Person(worker=True)
        person.state == 'awake'

        person = Person(worker=False)
        person.state == 'sleeping'


if __name__ == '__main__':
    unittest.main()
