"""Demonstrate a stoplight."""

import time

from fluidstate import StateChart


class StopLight(StateChart):
    """Proide an object representing a stoplight."""

    __statechart__ = {
        'name': 'stoplight',
        'initial': 'red',
        'states': [
            {
                'name': 'red',
                'transitions': [
                    {
                        'event': 'turn_green',
                        'target': 'green',
                        'action': lambda: time.sleep(3),
                    }
                ],
                'on_entry': lambda: print('Red light!'),
            },
            {
                'name': 'yellow',
                'transitions': [
                    {
                        'event': 'turn_red',
                        'target': 'red',
                        'action': lambda: time.sleep(3),
                    }
                ],
                'on_entry': lambda: print('Yellow light!'),
            },
            {
                'name': 'green',
                'transitions': [
                    {
                        'event': 'turn_yellow',
                        'target': 'yellow',
                        'action': lambda: time.sleep(3),
                    }
                ],
                'on_entry': lambda: print('Green light!'),
            },
        ],
    }


if __name__ == '__main__':
    import asyncio
    stoplight = StopLight()
    for x in range(3):
        stoplight.trigger('turn_green')
        stoplight.trigger('turn_yellow')
        stoplight.trigger('turn_red')
