import unittest
from fluidstate import StateMachine, state, transition


class JumperGuy(StateMachine):
    state('looking')
    state('falling')
    initial_state = 'looking'
    transition(source='looking', event='jump', target='falling')


class BooleanStateGettersSpec(unittest.TestCase):
    def test_it_has_boolean_getters_for_the_states(self):
        guy = JumperGuy()
        assert hasattr(guy, 'is_looking')
        assert hasattr(guy, 'is_falling')
        assert guy.current_state == 'looking'
        assert guy.current_state != 'falling'

        guy.jump()
        assert guy.current_state != 'looking'
        assert guy.current_state == 'falling'

    def test_it_has_boolean_getters_for_individual_states(self):
        guy = JumperGuy()
        guy.add_state('squashed')
        assert hasattr(guy, 'is_squashed')
        assert guy.current_state != 'squashed'

        guy.add_transition(source='falling', event='land', target='squashed')
        guy.jump()
        guy.land()
        assert guy.current_state == 'squashed'


if __name__ == '__main__':
    unittest.main()
