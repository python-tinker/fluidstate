import unittest
from fluidstate import StateMachine, state, transition


class CrazyGuy(StateMachine):
    state('looking', on_exit='no_lookin_anymore')
    state('falling', on_entry='will_fall_right_now')
    initial_state = 'looking'
    transition(
        before='looking',
        event='jump',
        after='falling',
        trigger='become_at_risk',
        guard='always_can_jump',
    )

    def __init__(self):
        StateMachine.__init__(self)
        self.at_risk = False
        self.callbacks = []

    def become_at_risk(self):
        self.at_risk = True
        self.callbacks.append('trigger')

    def no_lookin_anymore(self):
        self.callbacks.append('old on_exit')

    def will_fall_right_now(self):
        self.callbacks.append('new pre')

    def always_can_jump(self):
        self.callbacks.append('guard')
        return True


class CallbackOrder(unittest.TestCase):
    def setUp(self):
        guy = CrazyGuy()
        guy.jump()
        self.callbacks = guy.callbacks

    def test_it_runs_guard_first(self):
        """(1) guard"""
        self.callbacks[0] == 'guard'

    def test_it_and_then_old_state_on_exit(self):
        """(2) old state on_exit trigger"""
        self.callbacks[1] == 'old on_exit'

    def test_it_and_then_new_state_on_exit(self):
        """(3) new state pre trigger"""
        self.callbacks[2] == 'new pre'

    def test_it_and_then_transtrigger_trigger(self):
        """(4) transtrigger trigger"""
        self.callbacks[3] == 'trigger'


if __name__ == '__main__':
    unittest.main()
