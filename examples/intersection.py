"""Demonstrate a stoplight."""

import time

from fluidstate import StateMachine, state, transition


class StopLight(StateMachine):
    """Proide an object representing a stoplight."""

    state('red', on_entry=lambda: print('Red Light!'))
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
        trigger=lambda: time.sleep(2),
    )
    transition(
        'turn_red',
        before='yellow',
        after='red',
        trigger=lambda: time.sleep(5),
    )


class Intersection(StateMachine):
    """Provide an object representing an intersection."""

    state('north_south', on_exit='_change_red', machine=StopLight())
    state(
        'east_west',
        on_exit='_change_red',
        machine=StopLight(initial_state='green'),
    )

    initial_state: str = 'east_west'

    transition(
        event='allow_north_south',
        before='east_west',
        after='north_south',
        trigger='_change_green',
    )
    transition(
        event='allow_east_west',
        before='north_south',
        after='east_west',
        trigger='_change_green',
    )

    def _change_red(self) -> None:
        print(f"turning intersection {self.state} red")
        if self.state.machine:
            self.state.machine.turn_yellow()
            self.state.machine.turn_red()
        else:
            raise Exception('missing stoplight')

    def _change_green(self) -> None:
        print(f"turning intersection {self.state} green")
        if self.state.machine:
            self.state.machine.turn_green()
            self.change_light()
        else:
            raise Exception('missing stoplight')

    def change_light(self) -> None:
        """Start timing length of red light."""
        if self.state == 'north_south':
            print(intersection.state)
            self.allow_east_west()
        if self.state == 'east_west':
            print(intersection.state)
            self.allow_north_south()


if __name__ == '__main__':
    intersection = Intersection()
    intersection.change_light()
