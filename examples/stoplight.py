"""Demonstrate a stoplight."""

import time

from fluidstate import StateMachine, state, transition


class StopLight(StateMachine):
    """Proide an object representing a stoplight."""

    state('red', on_entry=lambda: print('Red light!'))
    state('yellow', on_entry=lambda: print('Yellow light!'))
    state('green', on_entry=lambda: print('Green light!'))

    initial_state: str = 'red'

    transition(
        'turn_green',
        before='red',
        after='green',
        trigger=lambda: time.sleep(5),
    )
    transition(
        'turn_yellow',
        before='green',
        after='yellow',
        trigger=lambda: time.sleep(5),
    )
    transition(
        'turn_red',
        before='yellow',
        after='red',
        trigger=lambda: time.sleep(5),
    )


if __name__ == '__main__':
    stoplight = StopLight()
    for x in range(3):
        stoplight.turn_green()
        stoplight.turn_yellow()
        stoplight.turn_red()
