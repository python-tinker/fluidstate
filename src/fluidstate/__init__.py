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

"""Compact statechart that can be vendored."""

from __future__ import annotations

import inspect
import logging
from collections import deque
from collections.abc import Callable, Iterable, Iterator
from itertools import zip_longest
from typing import Any, Optional, Union

__author__ = 'Jesse P. Johnson'
__author_email__ = 'jpj6652@gmail.com'
__title__ = 'fluidstate'
__description__ = 'Compact statechart that can be vendored.'
__version__ = '1.3.1a0'
__license__ = 'MIT'
__copyright__ = 'Copyright 2022 Jesse Johnson.'
__all__ = ('Action', 'Guard', 'State', 'StateChart', 'Transition')

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

Content = Union[Callable, str]
Condition = Union[Content, bool]


def tuplize(value: Any) -> tuple[Any, ...]:
    """Convert any type into a tuple."""
    return tuple(value) if type(value) in (list, tuple) else (value,)


class Action:
    """Encapsulate executable content."""

    def __init__(self, content: Content) -> None:
        self.content = content

    def __call__(
        self,
        machine: StateChart,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run action."""
        if callable(self.content):
            content = self.content
            args = (machine, *args)
        else:
            content = getattr(machine, self.content)
        parameters = inspect.signature(content).parameters
        if len(parameters.keys()) != 0:
            if kwargs and 'kwargs' not in parameters:
                kwargs = {k: v for k, v in kwargs.items() if k in parameters}
            return content(*args, **kwargs)
        return content()

    @classmethod
    def create(
        cls, settings: Union[Action, Callable, dict[str, Any]]
    ) -> 'Action':
        """Create action from configuration settings."""
        if isinstance(settings, cls):
            return settings
        if callable(settings) or isinstance(settings, str):
            return cls(settings)
        if isinstance(settings, dict):
            return cls(**settings)
        raise InvalidConfig('could not find a valid configuration for action')


class Guard:
    """Control the flow of transitions to states with conditions."""

    def __init__(self, condition: Condition) -> None:
        self.condition = condition

    def __call__(self, machine: StateChart, *args: Any, **kwargs: Any) -> bool:
        """Evaluate condition."""
        if callable(self.condition):
            return self.condition(machine, *args, **kwargs)
        if isinstance(self.condition, str):
            cond = getattr(machine, self.condition)
            if callable(cond):
                parameters = inspect.signature(cond).parameters
                if len(parameters.keys()) != 0:
                    if kwargs and 'kwargs' not in parameters:
                        kwargs = {
                            k: v for k, v in kwargs.items() if k in parameters
                        }
                    return cond(*args, **kwargs)
                return cond()
            return bool(cond)
        if isinstance(self.condition, bool):
            return self.condition
        return False

    @classmethod
    def create(
        cls, settings: Union[Guard, Callable, dict[str, Any], bool]
    ) -> Guard:
        """Create guard from configuration settings."""
        if isinstance(settings, cls):
            return settings
        if callable(settings) or isinstance(settings, str):
            return cls(settings)
        if isinstance(settings, dict):
            return cls(**settings)
        if isinstance(settings, bool):
            return cls(condition=settings)
        raise InvalidConfig('could not find a valid configuration for guard')


class Transition:
    """Provide transition capability for transitions."""

    def __init__(
        self,
        event: str,
        target: str,
        action: Optional[Iterable[Action]] = None,
        cond: Optional[Iterable[Guard]] = None,
    ) -> None:
        self.event = event
        self.target = target
        self.action = action or []
        self.cond = cond or []

    def __repr__(self) -> str:
        return repr(f"Transition(event={self.event}, target={self.target})")

    @classmethod
    def create(cls, settings: Union[Transition, dict]) -> Transition:
        """Consolidate."""
        if isinstance(settings, cls):
            return settings
        if isinstance(settings, dict):
            return cls(
                event=settings['event'],
                target=settings['target'],
                action=(
                    tuple(map(Action.create, tuplize(settings['action'])))
                    if 'action' in settings
                    else None
                ),
                cond=(
                    tuple(map(Guard.create, tuplize(settings['cond'])))
                    if 'cond' in settings
                    else None
                ),
            )
        raise InvalidConfig('could not find a valid transition configuration')

    def evaluate(self, machine: StateChart, *args: Any, **kwargs: Any) -> bool:
        """Evaluate guard conditions to determine correct transition."""
        result = True
        if self.cond:
            for cond in self.cond:
                result = cond(machine, *args, **kwargs)
                if not result:
                    break
        return result

    def execute(self, machine: StateChart, *args: Any, **kwargs: Any) -> None:
        """Execute actions of the transition."""
        if self.action:
            for action in self.action:
                action(machine, *args, **kwargs)
            log.info("executed action event for %r", self.event)
        else:
            log.info("no action event for %r", self.event)

    def run(self, machine: StateChart, *args: Any, **kwargs: Any) -> None:
        """Transition the state of the statechart."""
        relpath = machine.get_relpath(self.target)
        if relpath == '.':  # handle self transition
            machine.state._run_on_exit(machine)
            self.execute(machine, *args, **kwargs)
            machine.state._run_on_entry(machine)
        else:
            macrostep = relpath.split('.')[2 if relpath.endswith('.') else 1 :]
            while macrostep[0] == '':  # reverse
                machine.state._run_on_exit(machine)
                machine.state = machine.active[1]
                macrostep.pop(0)
            self.execute(machine, *args, **kwargs)
            for microstep in macrostep:  # forward
                try:
                    if (
                        isinstance(machine.state, State)
                        and microstep in machine.state.substates
                    ):
                        state = machine.get_state(microstep)
                        machine.state = state
                        state._run_on_entry(machine)
                    else:
                        raise InvalidState(
                            f"statepath not found: {self.target}"
                        )
                except FluidstateException as err:
                    log.error(err)
                    raise KeyError('superstate is undefined') from err
        log.info('changed state to %s', self.target)


class State:  # pylint: disable=too-many-instance-attributes
    """Represent state."""

    __initial: Optional[Content]
    __on_entry: Optional[Iterable[Action]]
    __on_exit: Optional[Iterable[Action]]
    __queue: deque[State]
    __superstate: Optional[State]
    __substates: tuple[State, ...]
    __transitions: tuple[Transition, ...]

    def __init__(
        self,
        name: str,
        transitions: Optional[tuple[Transition]] = None,
        states: Optional[tuple[State]] = None,
        **kwargs: Any,
    ) -> None:
        if not name.replace('_', '').isalnum():
            raise InvalidConfig('state name contains invalid characters')
        self.name = name
        self.__superstate: Optional[State] = None
        self.__type = kwargs.get('type')
        self.__initial = kwargs.get('initial')
        self.__substates = states or ()
        for state in self.substates:
            state.superstate = self
        self.__transitions = transitions or ()
        # FIXME: pseudostates should not include triggers
        self.__on_entry = kwargs.get('on_entry')
        self.__on_exit = kwargs.get('on_exit')
        self.__validate_state()

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return False

    def __repr__(self) -> str:
        return repr(f"State({self.name})")

    def __str__(self) -> str:
        return f"State({self.name})"

    def __iter__(self) -> State:
        self.__queue = deque([self])
        return self

    def __next__(self) -> State:
        # simple breadth-first iteration
        if self.__queue:
            x = self.__queue.pop()
            if isinstance(x, State):
                self.__queue.extendleft(x.substates)
            return x
        raise StopIteration

    def __reversed__(self) -> Iterator[State]:
        target: Optional[State] = self
        while target:
            yield target
            target = target.superstate

    def __validate_state(self) -> None:
        # TODO: empty statemachine should default to null event
        if self.type == 'compound':
            if len(self.__substates) < 2:
                raise InvalidConfig(
                    'There must be at least two states', self.name
                )
        if self.type == 'final' and self.__on_exit:
            log.warning('final state will never run "on_exit" action')
        log.info('evaluated state')

    @classmethod
    def create(cls, settings: Union[State, dict, str]) -> State:
        """Consolidate."""
        if isinstance(settings, cls):
            return settings
        if isinstance(settings, str):
            return cls(settings)
        if isinstance(settings, dict):
            return settings.get('factory', cls)(
                name=settings['name'],
                initial=settings.get('initial'),
                type=settings.get('type'),
                states=(
                    tuple(map(State.create, settings.pop('states')))
                    if 'states' in settings
                    else None
                ),
                transitions=(
                    tuple(map(Transition.create, settings['transitions']))
                    if 'transitions' in settings
                    else None
                ),
                on_entry=(
                    tuple(map(Action.create, tuplize(settings['on_entry'])))
                    if 'on_entry' in settings
                    else None
                ),
                on_exit=(
                    tuple(map(Action.create, tuplize(settings['on_exit'])))
                    if 'on_exit' in settings
                    else None
                ),
            )
        raise InvalidConfig('could not find a valid state configuration')

    @property
    def initial(self) -> Optional[Content]:
        """Return initial substate if defined."""
        return self.__initial

    @property
    def type(self) -> str:
        """Return state type."""
        if self.__type:
            return self.__type
        if self.substates:
            return 'compound'
        return 'atomic'

    @property
    def path(self) -> str:
        """Get the statepath of this state."""
        return '.'.join(reversed([x.name for x in reversed(self)]))

    @property
    def substates(self) -> tuple[State, ...]:
        """Return substates."""
        return self.__substates

    @property
    def superstate(self) -> Optional[State]:
        """Get superstate state."""
        return self.__superstate

    @superstate.setter
    def superstate(self, state: State) -> None:
        if self.__superstate is None:
            self.__superstate = state
        else:
            raise FluidstateException('cannot change superstate for state')

    @property
    def transitions(self) -> tuple[Transition, ...]:
        """Return transitions of this state."""
        return self.__transitions

    def _run_on_entry(self, machine: StateChart) -> None:
        for action in self.__on_entry or ():
            action(machine)
            log.info(
                "executed 'on_entry' state change action for %s", self.name
            )
        for transition in self.transitions:
            if transition.event == '':
                machine.trigger(transition.event)
                break

    def _run_on_exit(self, machine: StateChart) -> None:
        for action in self.__on_exit or ():
            action(machine)
            log.info(
                "executed 'on_exit' state change action for %s", self.name
            )


class MetaStateChart(type):
    """Provide capability to populate configuration for statemachine ."""

    main: State

    def __new__(
        mcs,
        name: str,
        bases: tuple[type, ...],
        attrs: dict[str, Any],
    ) -> MetaStateChart:
        settings = attrs.pop('__statechart__', None)
        obj = super().__new__(mcs, name, bases, attrs)
        if settings:
            obj.main = settings.pop('factory', State)(
                name=settings.pop('name', 'main'),
                initial=settings.pop('initial', None),
                type=settings.pop('type', None),
                states=(
                    tuple(map(State.create, settings.pop('states')))
                    if 'states' in settings
                    else None
                ),
                transitions=(
                    tuple(map(Transition.create, settings.pop('transitions')))
                    if 'transitions' in settings
                    else None
                ),
            )
        return obj


class StateChart(metaclass=MetaStateChart):
    """Provide state management capability."""

    __initial: State

    def __init__(
        self,
        initial: Optional[Union[Callable, str]] = None,
        **kwargs: Any,
    ) -> None:
        if 'logging_enabled' in kwargs and kwargs['logging_enabled']:
            handler = logging.StreamHandler()
            handler.setFormatter(
                logging.Formatter(
                    fmt=' %(name)s :: %(levelname)-8s :: %(message)s'
                )
            )
            log.addHandler(handler)
            if 'logging_level' in kwargs:
                log.setLevel(kwargs['logging_level'].upper())
        log.info('initializing statemachine')

        if hasattr(self.__class__, 'main'):
            self.__state = self.__class__.main
        else:
            raise InvalidConfig(
                'attempted initialization with empty superstate'
            )

        current = initial or self.main.initial
        if current:
            self.__state = self.get_state(
                current(self) if callable(current) else current
            )
        elif self.states:
            self.__state = self.states[0]
        else:
            raise InvalidConfig('an initial state must exist for statechart')
        log.info('loaded states and transitions')

        if kwargs.get('enable_start_transition', True):
            self.state._run_on_entry(self)
            # self.__process_eventless_transition()
        log.info('statemachine initialization complete')

    def __getattr__(self, name: str) -> Any:
        # ignore private attribute lookups
        if name.startswith('__'):
            raise AttributeError

        # handle state check for active states
        if name.startswith('is_'):
            return name[3:] in self.active

        raise AttributeError(f"unable to find {name!r} attribute")

    @property
    def active(self) -> tuple[State, ...]:
        """Return active states."""
        return tuple(reversed(self.state))

    @property
    def transitions(self) -> Iterator[Transition]:
        """Return list of current transitions."""
        for state in self.active:
            yield from state.transitions

    @property
    def superstate(self) -> State:
        """Return superstate."""
        return self.state.superstate or self.main

    @property
    def states(self) -> tuple[State, ...]:
        """Return list of states."""
        return self.superstate.substates

    @property
    def state(self) -> State:
        """Get the current state."""
        return self.__state

    @state.setter
    def state(self, state: State) -> None:
        """Set the current state."""
        if (
            state in self.state.substates
            or (len(self.active) > 1 and self.active[1] == state)
        ):
            self.__state = state
        else:
            raise InvalidTransition('cannot transition from final state')

    def get_relpath(self, target: str) -> str:
        """Get relative statepath of target state to current state."""
        if target in ('', self.state):  # self reference
            relpath = '.'
        else:  # need to determine if state is ascendent of descendent
            path = ['']
            source_path = self.state.path.split('.')
            target_path = self.get_state(target).path.split('.')
            for i, x in enumerate(
                zip_longest(source_path, target_path, fillvalue='')
            ):  # match the paths to walk either up or down from current
                if x[0] != x[1]:
                    if x[0] != '':  # target is a descendent
                        path.extend(['' for x in source_path[i:]])
                    if x[1] == '':  # target is a ascendent
                        path.extend([''])
                    if x[1] != '':  # target is child of a ascendent
                        path.extend(target_path[i:])
                    if i == 0:
                        raise InvalidState(
                            f"no relative path exists for: {target!s}"
                        )
                    break
            relpath = '.'.join(path)
        return relpath

    def get_state(self, statepath: str) -> State:
        """Get state."""
        state: State = self.main
        macrostep = statepath.split('.')

        # general recursive search for single query
        if len(macrostep) == 1:
            for x in tuple(state):
                if x == macrostep[0]:
                    return x
        # set start point if using relative lookup
        elif statepath.startswith('.'):
            relative = len(statepath) - len(statepath.lstrip('.')) - 1
            state = self.active[relative:][0]
            macrostep = [state.name] + macrostep[relative + 1 :]

        # check relative lookup is done
        target = macrostep[-1]
        if target in ('', state):
            return state

        # path based search
        while state and macrostep:
            microstep = macrostep.pop(0)
            # skip if current state is at microstep
            if state == microstep:
                continue
            # return current state if target found
            if state == target:
                return state
            # walk path if exists
            if hasattr(state, 'states') and microstep in state.states:
                state = state.states[microstep]
                # check if target is found
                if not macrostep:
                    return state
            else:
                break
        raise InvalidState(f"state could not be found: {statepath}")

    def get_transitions(self, event: str) -> tuple[Transition, ...]:
        """Get each transition maching event."""
        return tuple(
            filter(
                lambda transition: transition.event == event, self.transitions
            )
        )

    def trigger(self, event: str, *args: Any, **kwargs: Any) -> None:
        # TODO: need to consider superstate transitions.
        if self.state.type == 'final':
            raise InvalidTransition('cannot transition from final state')

        transitions = self.get_transitions(event)
        if not transitions:
            raise InvalidTransition('no transitions match event')
        allowed = []
        for transition in transitions:
            if transition.evaluate(self, *args, **kwargs):
                allowed.append(transition)
        if not allowed:
            raise GuardNotSatisfied(
                'Guard is not satisfied for this transition'
            )
        if len(allowed) > 1:
            raise ForkedTransition(
                'More than one transition was allowed for this event'
            )
        log.info('processed guard for %s', allowed[0].event)
        allowed[0].run(self, *args, **kwargs)
        log.info('processed transition event %s', allowed[0].event)


class FluidstateException(Exception):
    """Provide base fluidstate exception."""


class InvalidConfig(FluidstateException):
    """Handle invalid state configuration."""


class InvalidTransition(FluidstateException):
    """Handle invalid transitions."""


class InvalidState(FluidstateException):
    """Handle invalid state transition."""


class GuardNotSatisfied(FluidstateException):
    """Handle failed guard check."""


class ForkedTransition(FluidstateException):
    """Handle multiple possible transiion paths."""
