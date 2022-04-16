import unittest
from fluidstate import StateMachine, state, transition


class Door(StateMachine):

    state('open')
    state('closed')
    state('broken')
    initial_state = 'closed'

    transition(source='closed', event='open', target='open')
    transition(source='open', event='close', target='closed')
    transition(source='closed', event='crack', target='broken')

    def __init__(self):
        self.state_changes = []
        super(Door, self).__init__()

    def changing_state(self, source, target):
        self.state_changes.append((source, target))


class StateChangeNotificationSpec(unittest.TestCase):
    def test_notify_state_changes(self):
        door = Door()
        door.open()
        door.close()
        door.crack()
        door.state_changes == [
            ('closed', 'open'),
            ('open', 'closed'),
            ('closed', 'broken'),
        ]
