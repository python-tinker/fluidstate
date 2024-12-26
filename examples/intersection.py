"""Demonstrate a stoplight."""

import time

from fluidstate import Action, State, StateChart, Transition


def get_stoplight(name: str, initial: str = 'red') -> State:
    """Get a stoplight state machine."""
    return State(
        name=name,
        initial=initial,
        states=[
            State(
                name='red',
                transitions=[
                    Transition(
                        event='turn_green',
                        target='green',
                        action=[Action(lambda: time.sleep(5))],
                    )
                ],
                on_entry=Action(lambda: print('Red Light!')),
            ),
            State(
                name='yellow',
                transitions=[
                    Transition(
                        event='turn_red',
                        target='red',
                        action=[Action(lambda: time.sleep(5))],
                    )
                ],
                on_entry=Action(lambda: print('Yellow light!')),
            ),
            State(
                name='green',
                transitions=[
                    Transition(
                        event='turn_yellow',
                        target='yellow',
                        action=[Action(lambda: time.sleep(2))],
                    )
                ],
                on_entry=Action(lambda: print('Green light!')),
            ),
        ],
    )


class Intersection(StateChart):
    """Provide an object representing an intersection."""

    __statechart__ = {
        'name': 'intersection',
        'type': 'parallel',
        'states': [
            get_stoplight('north_sourth', 'red'),
            get_stoplight('east_west', 'green'),
        ],
    }

    def _change_red(self) -> None:
        print(f"turning intersection {self.state} red")
        if self.state:
            self.turn_yellow()
            self.turn_red()
        else:
            raise Exception('missing stoplight')

    def _change_green(self) -> None:
        print(f"turning intersection {self.state} green")
        if self.state:
            self.turn_green()
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
