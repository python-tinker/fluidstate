import unittest

from fluidstate import StateMachine, state, transition


class CrazyGuy(StateMachine):
    state('looking')
    state('falling')
    initial_state = 'looking'
    transition(
        source='looking',
        event='jump',
        target='falling',
        trigger=['become_at_risk', 'accelerate'],
    )

    def __init__(self):
        StateMachine.__init__(self)
        self.at_risk = False
        self.accelerating = False

    def become_at_risk(self):
        self.at_risk = True

    def accelerate(self):
        self.accelerating = True


class FluidityTransitionAction(unittest.TestCase):
    def test_it_runs_when_transition_occurs(self):
        guy = CrazyGuy()
        assert guy.at_risk is False

        guy.jump()
        assert guy.at_risk is True

    def test_it_supports_multiple_transition_triggers(self):
        guy = CrazyGuy()
        assert guy.at_risk is False
        assert guy.accelerating is False

        guy.jump()
        assert guy.at_risk is True
        assert guy.accelerating is True


if __name__ == '__main__':
    unittest.main()
