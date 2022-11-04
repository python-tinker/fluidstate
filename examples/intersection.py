"""Demonstrate a stoplight."""

import time

from fluidstate import StateChart, create_machine


stoplight = create_machine(
    {
        'initial': 'red',
        'states': [
            {
                'name': 'red',
                'transitions': [
                    {
                        'event': 'turn_green',
                        'target': 'green',
                        'action': lambda: time.sleep(5),
                    }
                ],
                'on_entry': lambda: print('Red Light!'),
            },
            {
                'name': 'yellow',
                'transitions': [
                    {
                        'event': 'turn_red',
                        'target': 'red',
                        'action': lambda: time.sleep(5),
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
                        'action': lambda: time.sleep(2),
                    }
                ],
                'on_entry': lambda: print('Green light!'),
            },
        ],
    }
)


class Intersection(StateChart):
    """Provide an object representing an intersection."""

    create_machine(
        {
            'initial': 'east_west',
            'states': [
                {
                    'name': 'north_south',
                    'transitions': [
                        {
                            'event': 'allow_east_west',
                            'target': 'east_west',
                            'action': '_change_green',
                        }
                    ],
                    'on_exit': '_change_red',
                    'states': [stoplight],
                },
                {
                    'name': 'east_west',
                    'transitions': [
                        {
                            'event': 'allow_north_south',
                            'target': 'north_south',
                            'action': '_change_green',
                        }
                    ],
                    'on_exit': '_change_red',
                    'states': [stoplight],
                },
            ],
        }
    )

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
