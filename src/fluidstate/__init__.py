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
__all__ = ('StateChart', 'State', 'Transition', 'states', 'transitions')

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

EventAction = Union[str, Callable]
EventActions = Union[EventAction, Iterable[EventAction]]
GuardCondition = Union[str, Callable]
GuardConditions = Union[GuardCondition, Iterable[GuardCondition]]
StateType = str
StateTypes = Union[StateType, Iterable[StateType]]

STATES: List['State'] = []


def transitions(*args: Any) -> List['Transition']:
    transitions: List['Transition'] = []
    for arg in args:
        if isinstance(arg, Transition):
            transitions.append(arg)
        if isinstance(arg, dict):
            transitions.append(
                Transition(
                    event=arg['event'],
                    target=arg['target'],
                    action=arg.get('action'),
                    cond=arg.get('cond'),
                )
            )
    return transitions


def states(*args: Any) -> List['State']:
    def add_states(*state_args: Any) -> List['State']:
        states = []
        for arg in state_args:
            if isinstance(arg, State):
                state = arg
            if isinstance(arg, dict):
                if 'states' in args:
                    machine = StateChart(states=add_states(arg['states']))
                else:
                    machine = None
                state = State(
                    name=arg['name'],
                    transitions=arg['transitions'],
                    on_entry=arg.get('on_entry'),
                    on_exit=arg.get('on_exit'),
                    machine=machine,
                )
            states.append(state)
        return states

    # TODO: need to do conditional return based on state context
    STATES.extend(add_states(*args))
    return STATES


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
    __states: Dict[str, 'State']
    initial: str

    def __new__(cls, *args: Any, **kwargs: Any) -> 'StateChart':
        obj = super(StateChart, cls).__new__(cls)
        obj.__states = {}
        return obj

    def __init__(
        self,
        initial: Optional[str] = None,
        states: List['State'] = [],
        **kwargs: Any,
    ) -> None:
        if 'logging_enabled' in kwargs and kwargs.get('logging_enabled'):
            for handler in log.handlers[:]:
                log.removeHandler(handler)
            log.addHandler(logging.StreamHandler())
        log.info('initializing statemachine')

        # TODO: attempt defining as class variable first
        if states != []:
            self.__states = {s.name: s for s in states}
        else:
            self.__states.update(self.__class__._class_states)
        self._evaluate_machine()
        log.info('loaded states and transitions')

        if initial:
            self.initial = initial
        elif callable(self.initial):
            self.initial = self.initial()

        self.__state = self.get_state(self.initial)
        self.__state._run_on_entry(self)
        for state in self.states:
            self.__register_state_callback(state)
        log.info('statemachine initialization complete')

    def __getattr__(self, name: str) -> Any:
        try:
            for x in self.state.transitions:
                if x.event == name:
                    return x.callback()
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

    def get_state(self, name: str) -> 'State':
        for state in self.states:
            if state.name == name:
                return state
        raise InvalidState(f"state could not be found: {name}")

    def _update_state(self, state: str) -> None:
        self.__state = self.get_state(state)
        log.info(f"changed state to {state}")

    def add_state(
        self,
        name: str,
        transitions: List[Dict[str, Any]] = [],
        on_entry: Optional[EventActions] = None,
        on_exit: Optional[EventActions] = None,
        machine: Optional['StateChart'] = None,
    ) -> None:
        state = State(
            name=name,
            transitions=[
                Transition(
                    event=t['event'],
                    target=t['target'],
                    action=t.get('action'),
                    cond=t.get('cond'),
                )
                for t in transitions
            ],
            on_entry=on_entry,
            on_exit=on_exit,
            machine=machine,
        )
        self.__register_state_callback(state)
        self.__states[name] = state
        log.info(f"added state {name}")

    def add_transition(
        self,
        state: str,
        event: str,
        target: StateType,
        action: Optional[str] = None,
        cond: Optional[str] = None,
    ) -> None:
        transition = Transition(
            event=event,
            target=target,
            action=action,
            cond=cond,
        )
        self.get_state(state).add_transition(transition)
        self.__register_transition_callback(transition)
        log.info(f"added transition {event}")

    def _process_transitions(
        self, event: str, *args: Any, **kwargs: Any
    ) -> None:
        transitions = self.__state.get_transitions(event)
        if transitions == []:
            raise InvalidTransition('no transitions match event')
        transition = self._evaluate_guards(transitions)
        transition.run(self, *args, **kwargs)

    def _evaluate_guards(
        self, transitions: List['Transition']
    ) -> 'Transition':
        allowed_transitions = []
        for transition in transitions:
            if transition.evaluate(self):
                allowed_transitions.append(transition)
        if len(allowed_transitions) == 0:
            raise GuardNotSatisfied(
                'Guard is not satisfied for this transition'
            )
        elif len(allowed_transitions) > 1:
            raise ForkedTransition(
                'More than one transition was allowed for this event'
            )
        # XXX: assuming duplicate transition event names are desired then
        # result should exhaust possible matching guard transitions
        return allowed_transitions[0]


class State:
    __slots__ = ['__transitions', 'name', 'on_entry', 'on_exit', 'machine']

    def __init__(
        self,
        name: str,
        transitions: List['Transition'] = [],
        on_entry: Optional[EventActions] = None,
        on_exit: Optional[EventActions] = None,
        machine: Optional['StateChart'] = None,
    ) -> None:
        self.name = name
        self.__transitions = transitions
        self.on_entry = on_entry
        self.on_exit = on_exit
        self.machine = machine

    def __repr__(self) -> str:
        return repr(f"State({self.name})")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.name == other.name
        elif isinstance(other, str):
            return self.name == other
        return False

    @property
    def substate(self) -> Optional['State']:
        if self.machine:
            return self.machine.state
        return None

    @property
    def substates(self) -> Optional[List['State']]:
        if self.machine:
            return list(self.machine.states)
        return None

    @property
    def transitions(self) -> List['Transition']:
        return self.__transitions

    def add_transition(self, transition: 'Transition') -> None:
        self.__transitions.append(transition)

    def callback(self) -> Callable:
        def state_check(machine):
            return machine.state == self.name

        return state_check

    def get_transitions(self, event: str) -> List['Transition']:
        return list(
            filter(
                lambda transition: transition.event == event, self.transitions
            )
        )

    def _run_on_entry(self, machine: 'StateChart') -> None:
        if self.on_entry is not None:
            Action(machine).run(self.on_entry)
            log.info(
                f"executed 'on_entry' state change action for {self.name}"
            )

    def _run_on_exit(self, machine: 'StateChart') -> None:
        if self.on_exit is not None:
            Action(machine).run(self.on_exit)
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

        event.__doc__ = f"event {self.event}"
        event.__name__ = self.event
        return event

    def evaluate(self, machine: 'StateChart') -> bool:
        return Guard(machine).evaluate(self.cond) if self.cond else True

    def run(self, machine: 'StateChart', *args: Any, **kwargs: Any) -> None:
        machine.state._run_on_exit(machine)
        machine._update_state(self.target)
        machine.get_state(self.target)._run_on_entry(machine)
        if self.action:
            Action(machine).run(self.action, *args, **kwargs)
            log.info(f"executed action event for '{self.event}'")
        else:
            log.info(f"no action event for '{self.event}'")


class Action:
    __slots__ = ['machine']

    def __init__(self, machine: 'StateChart') -> None:
        self.machine = machine

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
            self.__run_with_args(action, self.machine, *args, **kwargs)
        else:
            self.__run_with_args(
                getattr(self.machine, action), *args, **kwargs
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
