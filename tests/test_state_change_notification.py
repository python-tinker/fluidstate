import unittest

from fluidstate import StateMachine, state, transition


class Door(StateMachine):

    state('open')
    state('closed')
    state('broken')
    initial_state = 'closed'

    transition(before='closed', event='open', after='open')
    transition(before='open', event='close', after='closed')
    transition(before='closed', event='crack', after='broken')

    def __init__(self):
        self.state_changes = []
        super(Door, self).__init__()

    def changing_state(self, before, after):
        self.state_changes.append((before, after))


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
