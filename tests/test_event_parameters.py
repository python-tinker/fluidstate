import unittest
from fluidstate import StateMachine, state, transition


class Door(StateMachine):
    state('closed')
    state('open')
    initial_state = 'closed'
    transition(
        before='closed', event='open', after='open', trigger='open_trigger'
    )
    transition(
        before='open',
        event='close',
        after='closed',
        trigger='close_trigger',
    )

    def open_trigger(self, when, where):
        self.when = when
        self.where = where

    def close_trigger(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs


class EventParameters(unittest.TestCase):
    def test_it_pass_parameters_received_by_event_to_trigger(self):
        door = Door()
        door.open('now!', 'there!')
        assert hasattr(door, 'when')
        assert door.when == 'now!'
        assert hasattr(door, 'where')
        assert door.where == 'there!'

    def test_it_pass_args_and_kwargs_to_trigger(self):
        door = Door()
        door.open('anytime', 'anywhere')
        door.close('1', 2, object, test=9, it=8, works=7)
        assert hasattr(door, 'args')
        assert door.args == ('1', 2, object)
        assert hasattr(door, 'kwargs')
        assert door.kwargs == {'test': 9, 'it': 8, 'works': 7}


if __name__ == '__main__':
    unittest.main()
