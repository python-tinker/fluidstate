# Copyright (c) 2022 Jesse P. Johnson
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Compact state machine that can be vendored."""

import logging
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple, Union

__author__ = 'Jesse P. Johnson'
__author_email__ = 'jpj6652@gmail.com'
__title__ = 'fluidstate'
__description__ = 'Compact statechart that can be vendored.'
__version__ = '1.0.0b2'
__license__ = 'MIT'
__copyright__ = 'Copyright 2022 Jesse Johnson.'
__all__ = (
    'StateChart',
    'State',
    'Transition',
    'states',
    'state',
    'transitions',
    'transition',
)

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

EventAction = Union[str, Callable]
EventActions = Union[EventAction, Iterable[EventAction]]
GuardCondition = Union[str, Callable]
GuardConditions = Union[GuardCondition, Iterable[GuardCondition]]
StateType = str
StateTypes = Union[StateType, Iterable[StateType]]

STATES: List['State'] = []


def transition(arg: Union['Transition', dict]) -> 'Transition':
    if isinstance(arg, Transition):
        return arg
    if isinstance(arg, dict):
        return Transition(
            event=arg['event'],
            target=arg['target'],
            action=arg.get('action'),
            cond=arg.get('cond'),
        )
    raise InvalidConfig('could not find valid transition configuration')


def transitions(*args: Any) -> List['Transition']:
    return list(map(transition, args))


def state(arg: Union['State', dict, str]) -> 'State':
    if isinstance(arg, State):
        return arg
    elif isinstance(arg, str):
        return State(arg)
    elif isinstance(arg, dict):
        return State(
            name=arg['name'],
            transitions=transitions(arg.get('transitions', [])),
            on_entry=arg.get('on_entry'),
            on_exit=arg.get('on_exit'),
        )
    raise InvalidConfig('could not find valid state configuration')


def states(*args: Any, **kwargs: Any) -> List['State']:
    _states = list(map(state, args))
    if kwargs.get('update_global', True):
        global STATES
        STATES.extend(_states)
        return STATES
    else:
        return _states


def tuplize(value: Any) -> Tuple[Any, ...]:
    return tuple(value) if type(value) in [list, tuple] else (value,)


class MetaStateChart(type):
    _class_states: Dict[str, 'State']

    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
    ) -> 'MetaStateChart':
        global STATES
        obj = super(MetaStateChart, cls).__new__(cls, name, bases, attrs)
        obj._class_states = {s.name: s for s in STATES}
        STATES = []
        return obj


class StateChart(metaclass=MetaStateChart):
    __slots__ = ['initial', '__states', '__dict__']
    initial: Union[Callable, str]

    def __init__(
        self,
        initial: Optional[Union[Callable, str]] = None,
        states: List['State'] = [],
        **kwargs: Any,
    ) -> None:
        if 'logging_enabled' in kwargs and kwargs.get('logging_enabled'):
            for handler in log.handlers[:]:
                log.removeHandler(handler)
            log.addHandler(logging.StreamHandler())
        log.info('initializing statemachine')

        self.__traverse_states = kwargs.get('traverse_states', False)

        self.__states: Dict[str, 'State'] = {}
        self.__states.update(self.__class__._class_states)
        if states != []:
            self.__states.update({s.name: s for s in states})
        self._evaluate_machine()
        log.info('loaded states and transitions')

        if initial:
            self.initial = initial
        if callable(self.initial):
            self.initial = self.initial()

        self.__state = self.get_state(str(self.initial))
        self.__state._run_on_entry(self)
        for state in self.states:
            self.__register_state_callback(state)
        log.info('statemachine initialization complete')

    def __getattr__(self, name: str) -> Any:
        try:
            for x in self.state.transitions:
                if x.event == name:
                    return x.callback()
            if self.__traverse_states:
                for key, value in self.__states.items():
                    if key == name:
                        return self.__items[name]
            else:
                raise KeyError
        except KeyError:
            raise AttributeError

    def __register_transition_callback(self, transition: 'Transition') -> None:
        setattr(
            self,
            transition.event,
            transition.callback().__get__(self, self.__class__),
        )

    def __register_state_callback(self, state: 'State') -> None:
        setattr(
            self,
            f"is_{state.name}",
            state.callback().__get__(self, self.__class__),
        )
        for transition in state.transitions:
            self.__register_transition_callback(transition)

    def _evaluate_machine(self) -> None:
        # TODO: empty statemachine should default to null event
        if len(self.__states) < 2:
            raise InvalidConfig('There must be at least two states')
        if not getattr(self, 'initial', None):
            raise InvalidConfig('There must exist an initial state')
        log.info('evaluated statemachine')

    @property
    def transitions(self) -> List['Transition']:
        return self.state.transitions

    @property
    def states(self) -> List['State']:
        return list(self.__states.values())

    @property
    def state(self) -> 'State':
        try:
            return self.__state
        except Exception:
            log.error('state is undefined')
            raise KeyError

    def get_state(self, query: str) -> 'State':
        for state in self.states:
            if state.name == query:
                return state
        raise InvalidState(f"state could not be found: {query}")

    # def get_state(self, query: str) -> 'Foo':
    #     paths = query.split('.')

    #     current = self
    #     for i, state in enumerate(paths):
    #         current = current.items[state]
    #         if i == (len(paths) - 1):
    #             return current
    #     raise InvalidState(f"state could not be found: {query}")

    def _change_state(self, state: str) -> None:
        self.state._run_on_exit(self)
        self.__state = self.get_state(state)
        self.__state._run_on_entry(self)
        log.info(f"changed state to {state}")

    def add_state(self, state: 'State') -> None:
        self.__register_state_callback(state)
        self.__states[state.name] = state
        log.info(f"added state {state.name}")

    def add_transition(self, transition: 'Transition', state: str) -> None:
        self.get_state(state).add_transition(transition)
        self.__register_transition_callback(transition)
        log.info(f"added transition {transition.event}")

    def _process_transitions(
        self, event: str, *args: Any, **kwargs: Any
    ) -> None:
        _transitions = self.__state.get_transitions(event)
        if _transitions == []:
            raise InvalidTransition('no transitions match event')
        _transition = self._evaluate_guards(_transitions)
        _transition.run(self, *args, **kwargs)

    def _evaluate_guards(
        self, transitions: List['Transition']
    ) -> 'Transition':
        allowed = []
        for _transition in transitions:
            if _transition.evaluate(self):
                allowed.append(_transition)
        if len(allowed) == 0:
            raise GuardNotSatisfied(
                'Guard is not satisfied for this transition'
            )
        elif len(allowed) > 1:
            raise ForkedTransition(
                'More than one transition was allowed for this event'
            )
        return allowed[0]


class State:
    __slots__ = [
        'name',
        'initial',
        '__states',
        '__transitions',
        '__on_entry',
        '__on_exit',
    ]
    initial: Optional[Union[Callable, str]]
    __on_entry: Optional[EventActions]
    __on_exit: Optional[EventActions]

    def __init__(
        self,
        name: str,
        transitions: List['Transition'] = [],
        states: List['State'] = [],
        **kwargs: Any,
    ) -> None:
        self.name = name
        self.__transitions = transitions
        self.__states = {x.name: x for x in states}
        self.__on_entry = kwargs.get('on_entry')
        self.__on_exit = kwargs.get('on_exit')
        self.initial = kwargs.get('initial')

    def __repr__(self) -> str:
        return repr(f"State({self.name})")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        return False

    # @property
    # def superstate(self) -> Optional['State']:
    #     return None

    # @property
    # def state(self) -> Optional['State']:
    #     return self.__state

    @property
    def states(self) -> Dict[str, 'State']:
        return self.__states

    @property
    def transitions(self) -> List['Transition']:
        return self.__transitions

    def add_transition(self, transition: 'Transition') -> None:
        self.__transitions.append(transition)

    def callback(self) -> Callable:
        def state_check(machine):
            return machine.state == self.name

        state_check.__name__ = self.name
        state_check.__doc__ = f"Show this: {self.name}."
        return state_check

    def get_transitions(self, event: str) -> List['Transition']:
        return list(
            filter(
                lambda transition: transition.event == event, self.transitions
            )
        )

    def _run_on_entry(self, machine: 'StateChart') -> None:
        if self.__on_entry is not None:
            Action(machine).run(self.__on_entry)
            log.info(
                f"executed 'on_entry' state change action for {self.name}"
            )

    def _run_on_exit(self, machine: 'StateChart') -> None:
        if self.__on_exit is not None:
            Action(machine).run(self.__on_exit)
            log.info(f"executed 'on_exit' state change action for {self.name}")


class Transition:
    __slots__ = ['event', 'target', 'action', 'cond']

    def __init__(
        self,
        event: str,
        target: str,
        action: Optional[EventActions] = None,
        cond: Optional[GuardConditions] = None,
    ) -> None:
        self.event = event
        self.target = target
        self.action = action
        self.cond = cond

    def __repr__(self) -> str:
        return repr(f"Transition(event={self.event}, target={self.target})")

    def callback(self) -> Callable:
        def event(machine, *args, **kwargs):
            machine._process_transitions(self.event, *args, **kwargs)
            log.info(f"processed {self.event}")

        event.__name__ = self.event
        event.__doc__ = f"Show event: {self.event}."
        return event

    def evaluate(self, machine: 'StateChart') -> bool:
        return Guard(machine).evaluate(self.cond) if self.cond else True

    def run(self, machine: 'StateChart', *args: Any, **kwargs: Any) -> None:
        machine._change_state(self.target)
        if self.action:
            Action(machine).run(self.action, *args, **kwargs)
            log.info(f"executed action event for '{self.event}'")
        else:
            log.info(f"no action event for '{self.event}'")


class Action:
    __slots__ = ['__machine']

    def __init__(self, machine: 'StateChart') -> None:
        self.__machine = machine

    def run(
        self,
        params: EventActions,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        for x in tuplize(params):
            self._run_action(x, *args, **kwargs)

    def _run_action(
        self, action: EventAction, *args: Any, **kwargs: Any
    ) -> None:
        if callable(action):
            self.__run_with_args(action, self.__machine, *args, **kwargs)
        else:
            self.__run_with_args(
                getattr(self.__machine, action), *args, **kwargs
            )

    @staticmethod
    def __run_with_args(action: Callable, *args: Any, **kwargs: Any) -> None:
        try:
            action(*args, **kwargs)
        except TypeError:
            action()


class Guard:
    __slots__ = ['__machine']

    def __init__(self, machine: 'StateChart') -> None:
        self.__machine = machine

    def evaluate(self, cond: GuardConditions) -> bool:
        result = True
        for x in tuplize(cond):
            result = result and self.__evaluate(self.__machine, x)
        return result

    @staticmethod
    def __evaluate(machine: 'StateChart', item: GuardCondition) -> bool:
        if callable(item):
            return item(machine)
        else:
            guard = getattr(machine, item)
            if callable(guard):
                guard = guard()
            return guard


class FluidstateException(Exception):
    pass


class InvalidConfig(FluidstateException):
    pass


class InvalidTransition(FluidstateException):
    pass


class InvalidState(FluidstateException):
    pass


class GuardNotSatisfied(FluidstateException):
    pass


class ForkedTransition(FluidstateException):
    pass
