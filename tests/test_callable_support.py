import unittest
from fluidity import StateMachine, state, transition
from fluidity import NeedNotSatisfied

footsteps = []


class Foo:
    def bar(self):
        footsteps.append('after looking')


foo = Foo()


def before_falling_function():
    footsteps.append('before falling')


class JumperGuy(StateMachine):
    state(
        'looking',
        before=lambda jumper: jumper.append('before looking'),
        after=foo.bar,
    )
    state('falling', before=before_falling_function)
    initial_state = 'looking'

    transition(
        source='looking',
        event='jump',
        target='falling',
        trigger=lambda jumper: jumper.append('trigger jump'),
        need=lambda jumper: jumper.append('need jump') is None,
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
                'before looking',
                'after looking',
                'before falling',
                'trigger jump',
                'need jump',
            ]
        )

    def test_it_should_deny_state_change_if_need_callable_returns_false(self):
        class Door(StateMachine):
            state('open')
            state('closed')
            initial_state = 'closed'
            transition(
                source='closed',
                event='open',
                target='open',
                need=lambda d: not door.locked,
            )

            def locked(self):
                return self.locked

        door = Door()
        door.locked = True
        with self.assertRaises(NeedNotSatisfied):
            door.open()


if __name__ == '__main__':
    unittest.main()
