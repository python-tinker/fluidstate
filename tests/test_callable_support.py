import unittest

from fluidstate import (
    GuardNotSatisfied,
    StateMachine,
    state,
    transition,
)

footsteps = []


class Foo:
    def bar(self):
        footsteps.append('on_exit looking')


foo = Foo()


def pre_falling_function():
    footsteps.append('pre falling')


class JumperGuy(StateMachine):
    state(
        'looking',
        on_entry=lambda jumper: jumper.append('pre looking'),
        on_exit=foo.bar,
    )
    state('falling', on_entry=pre_falling_function)
    initial_state = 'looking'

    transition(
        before='looking',
        event='jump',
        after='falling',
        trigger=lambda jumper: jumper.append('trigger jump'),
        guard=lambda jumper: jumper.append('guard jump') is None,
    )

    def __init__(self):
        StateMachine.__init__(self)

    def append(self, text):
        footsteps.append(text)


class CallableSupport(unittest.TestCase):
    def test_every_callback_can_be_a_callable(self):
        """every callback can be a callable"""
        guy = JumperGuy()
        guy.jump()
        assert len(footsteps) == 5
        assert sorted(footsteps) == sorted(
            [
                'pre looking',
                'on_exit looking',
                'pre falling',
                'trigger jump',
                'guard jump',
            ]
        )

    def test_it_should_deny_state_change_if_guard_callable_returns_false(self):
        class Door(StateMachine):
            state('open')
            state('closed')
            initial_state = 'closed'
            transition(
                before='closed',
                event='open',
                after='open',
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
