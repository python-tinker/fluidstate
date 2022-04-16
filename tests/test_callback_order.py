import unittest
from fluidstate import StateMachine, state, transition


class CrazyGuy(StateMachine):
    state('looking', after='no_lookin_anymore')
    state('falling', before='will_fall_right_now')
    initial_state = 'looking'
    transition(
        source='looking',
        event='jump',
        target='falling',
        trigger='become_at_risk',
        need='always_can_jump',
    )

    def __init__(self):
        StateMachine.__init__(self)
        self.at_risk = False
        self.callbacks = []

    def become_at_risk(self):
        self.at_risk = True
        self.callbacks.append('trigger')

    def no_lookin_anymore(self):
        self.callbacks.append('old after')

    def will_fall_right_now(self):
        self.callbacks.append('new before')

    def always_can_jump(self):
        self.callbacks.append('need')
        return True


class CallbackOrder(unittest.TestCase):
    def setUp(self):
        guy = CrazyGuy()
        guy.jump()
        self.callbacks = guy.callbacks

    def test_it_runs_need_first(self):
        """(1) need"""
        self.callbacks[0] == 'need'

    def test_it_and_then_old_state_after(self):
        """(2) old state after trigger"""
        self.callbacks[1] == 'old after'

    def test_it_and_then_new_state_after(self):
        """(3) new state before trigger"""
        self.callbacks[2] == 'new before'

    def test_it_and_then_transtrigger_trigger(self):
        """(4) transtrigger trigger"""
        self.callbacks[3] == 'trigger'


if __name__ == '__main__':
    unittest.main()
