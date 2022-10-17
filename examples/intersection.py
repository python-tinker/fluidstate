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
        target='green',
        action=lambda: time.sleep(5),
    )
    transition(
        'turn_yellow',
        target='yellow',
        action=lambda: time.sleep(2),
    )
    transition(
        'turn_red',
        target='red',
        action=lambda: time.sleep(5),
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
        target='north_south',
        action='_change_green',
    )
    transition(
        event='allow_east_west',
        target='east_west',
        action='_change_green',
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
