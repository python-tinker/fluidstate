import unittest

from fluidstate import StateChart, state, transition


class CrazyGuy(StateChart):
    state('looking')
    state('falling')
    initial_state = 'looking'
    transition(
        event='jump',
        target='falling',
        action=['become_at_risk', 'accelerate'],
    )

    def __init__(self):
        StateChart.__init__(self)
        self.at_risk = False
        self.accelerating = False

    def become_at_risk(self):
        self.at_risk = True

    def accelerate(self):
        self.accelerating = True


class FluidstateTransitionAction(unittest.TestCase):
    def test_it_runs_when_transition_occurs(self):
        guy = CrazyGuy()
        assert guy.at_risk is False

        guy.jump()
        assert guy.at_risk is True

    def test_it_supports_multiple_transition_actions(self):
        guy = CrazyGuy()
        assert guy.at_risk is False
        assert guy.accelerating is False

        guy.jump()
        assert guy.at_risk is True
        assert guy.accelerating is True


if __name__ == '__main__':
    unittest.main()
