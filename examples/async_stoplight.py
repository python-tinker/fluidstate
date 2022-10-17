"""Demonstrate a stoplight."""

import asyncio

from fluidstate import StateMachine, state, transition


class StopLight(StateMachine):
    """Proide an object representing a stoplight."""

    state('red', on_entry=lambda: print('Red light!'))
    state('yellow', on_entry=lambda: print('Yellow light!'))
    state('green', on_entry=lambda: print('Green light!'))

    initial_state: str = 'red'

    transition(
        'turn_green',
        target='green',
        action=lambda: asyncio.sleep(5),
    )
    transition(
        'turn_yellow',
        target='yellow',
        action=lambda: asyncio.sleep(2),
    )
    transition(
        'turn_red',
        target='red',
        action=lambda: asyncio.sleep(5),
    )


if __name__ == '__main__':
    stoplight = StopLight()
    while True:
        stoplight.turn_green()
        stoplight.turn_yellow()
        stoplight.turn_red()
