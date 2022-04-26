import unittest
from fluidstate import StateMachine, state, transition


class JumperGuy(StateMachine):
    state('looking')
    state('falling')
    initial_state = 'looking'
    transition(before='looking', event='jump', after='falling')


class BooleanStateGettersSpec(unittest.TestCase):
    def test_it_has_boolean_getters_for_the_states(self):
        guy = JumperGuy()
        assert hasattr(guy, 'is_looking')
        assert hasattr(guy, 'is_falling')
        assert guy.state == 'looking'
        assert guy.state != 'falling'

        guy.jump()
        assert guy.state != 'looking'
        assert guy.state == 'falling'

    def test_it_has_boolean_getters_for_individual_states(self):
        guy = JumperGuy()
        guy.add_state('squashed')
        assert hasattr(guy, 'is_squashed')
        assert guy.state != 'squashed'

        guy.add_transition(before='falling', event='land', after='squashed')
        guy.jump()
        guy.land()
        assert guy.state == 'squashed'


if __name__ == '__main__':
    unittest.main()
