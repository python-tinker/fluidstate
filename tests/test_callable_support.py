import unittest
from fluidity import StateMachine, state, transition
from fluidity import GuardNotSatisfied

footsteps = []


class Foo:
    def bar(self):
        footsteps.append('exit looking')


foo = Foo()


def entry_falling_function():
    footsteps.append('entry falling')


class JumperGuy(StateMachine):
    state(
        'looking',
        entry=lambda jumper: jumper.append('entry looking'),
        exit=foo.bar,
    )
    state('falling', entry=entry_falling_function)
    initial_state = 'looking'

    transition(
        source='looking',
        event='jump',
        target='falling',
        action=lambda jumper: jumper.append('action jump'),
        guard=lambda jumper: jumper.append('guard jump') is None,
    )

    def __init__(self):
        StateMachine.__init__(self)

    def append(self, text):
        footsteps.append(text)


class CallableSupport(unittest.TestCase):
    def test_every_callback_can_be_a_callable(self):
        '''every callback can be a callable'''
        guy = JumperGuy()
        guy.jump()
        assert len(footsteps) == 5
        assert sorted(footsteps) == sorted(
            [
                'entry looking',
                'exit looking',
                'entry falling',
                'action jump',
                'guard jump',
            ]
        )

    def test_it_should_deny_state_change_if_guard_callable_returns_false(self):
        class Door(StateMachine):
            state('open')
            state('closed')
            initial_state = 'closed'
            transition(
                source='closed',
                event='open',
                target='open',
                guard=lambda d: not door.locked,
            )

            def locked(self):
                return self.locked

        door = Door()
        door.locked = True
        with self.assertRaises(GuardNotSatisfied):
            door.open()


if __name__ == '__main__':
    unittest.main()
