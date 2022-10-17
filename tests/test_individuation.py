import unittest

from fluidstate import StateChart, state, transition


class Door(StateChart):
    state('closed')
    state('open')
    initial_state = 'closed'
    transition(event='open', target='open')


class IndividuationSpec(unittest.TestCase):
    """Fluidstate object (individuation)"""

    def setUp(self):
        self.door = Door()
        self.door.add_state('broken')
        self.door.add_transition(event='crack', target='broken')

    def test_it_responds_to_an_event(self):
        assert hasattr(self.door, 'crack')

    def test_its_event_changes_its_state_when_called(self):
        self.door.crack()
        assert self.door.state == 'broken'

    def test_it_informs_all_its_states(self):
        assert len(self.door.states) == 3
        assert self.door.states == ['closed', 'open', 'broken']

    def test_individuation_does_not_affect_other_objects_before_same_class(
        self,
    ):
        another_door = Door()
        assert not hasattr(another_door, 'crack')


if __name__ == '__main__':
    unittest.main()
