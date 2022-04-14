import unittest
from fluidity import StateMachine, state, transition


class CrazyGuy(StateMachine):
    state('looking', exit='no_lookin_anymore')
    state('falling', entry='will_fall_right_now')
    initial_state = 'looking'
    transition(
        source='looking',
        event='jump',
        target='falling',
        action='become_at_risk',
        guard='always_can_jump',
    )

    def __init__(self):
        StateMachine.__init__(self)
        self.at_risk = False
        self.callbacks = []

    def become_at_risk(self):
        self.at_risk = True
        self.callbacks.append('action')

    def no_lookin_anymore(self):
        self.callbacks.append('old exit')

    def will_fall_right_now(self):
        self.callbacks.append('new entry')

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

    def test_it_and_then_old_state_exit(self):
        """(2) old state exit action"""
        self.callbacks[1] == 'old exit'

    def test_it_and_then_new_state_exit(self):
        """(3) new state entry action"""
        self.callbacks[2] == 'new entry'

    def test_it_and_then_transaction_action(self):
        """(4) transaction action"""
        self.callbacks[3] == 'action'


if __name__ == '__main__':
    unittest.main()
