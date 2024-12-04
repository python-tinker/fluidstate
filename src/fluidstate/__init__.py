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

import inspect
import logging
from copy import deepcopy
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Tuple,
    Union,
)

__author__ = 'Jesse P. Johnson'
__author_email__ = 'jpj6652@gmail.com'
__title__ = 'fluidstate'
__description__ = 'Compact statechart that can be vendored.'
__version__ = '1.1.0a6'
__license__ = 'MIT'
__copyright__ = 'Copyright 2022 Jesse Johnson.'
__all__ = ('StateChart', 'State', 'Transition')

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

Content = Union[Callable, str]
Actions = Iterable['Action']
Guards = Iterable['Guard']


def tuplize(value: Any) -> Tuple[Any, ...]:
    """Convert any type into a tuple."""
    return tuple(value) if type(value) in (list, tuple) else (value,)


class Action:
    """Encapsulate executable content."""

    def __init__(self, content: 'Content') -> None:
        self.content = content

    @classmethod
    def create(
        cls, settings: Union['Action', Callable, Dict[str, Any]]
    ) -> 'Action':
        """Create expression from configuration."""
        if isinstance(settings, cls):
            return settings
        if callable(settings) or isinstance(settings, str):
            return cls(settings)
        if isinstance(settings, dict):
            return cls(**settings)
        raise InvalidConfig('could not find a valid configuration for action')

    def run(
        self,
        machine: 'StateChart',
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Run the action."""
        return self._run_action(machine, *args, **kwargs)

    def _run_action(
        self, machine: 'StateChart', *args: Any, **kwargs: Any
    ) -> Any:
        if callable(self.content):
            return self.__run_with_args(self.content, machine, *args, **kwargs)
        return self.__run_with_args(
            getattr(machine, self.content), *args, **kwargs
        )

    @staticmethod
    def __run_with_args(content: Callable, *args: Any, **kwargs: Any) -> Any:
        signature = inspect.signature(content)
        if len(signature.parameters.keys()) != 0:
            return content(*args, **kwargs)
        return content()


class Guard:
    """Control the flow of transitions to states with conditions."""

    def __init__(self, condition: 'Content') -> None:
        self.condition = condition

    @classmethod
    def create(
        cls, settings: Union['Guard', Callable, Dict[str, Any]]
    ) -> 'Guard':
        """Create expression from configuration."""
        if isinstance(settings, cls):
            return settings
        if callable(settings) or isinstance(settings, str):
            return cls(settings)
        if isinstance(settings, dict):
            return cls(**settings)
        raise InvalidConfig('could not find a valid configuration for guard')

    def evaluate(
        self, machine: 'StateChart', *args: Any, **kwargs: Any
    ) -> bool:
        """Evaluate conditions."""
        if callable(self.condition):
            return self.condition(machine, *args, **kwargs)
        if isinstance(self.condition, str):
            cond = getattr(machine, self.condition)
            if callable(cond):
                return self.__evaluate_with_args(cond, *args, **kwargs)
            return bool(cond)
        return False

    @staticmethod
    def __evaluate_with_args(
        condition: Callable, *args: Any, **kwargs: Any
    ) -> bool:
        signature = inspect.signature(condition)
        params = dict(signature.parameters)

        if len(params.keys()) != 0:
            # _kwargs = {k: v for k, v in kwargs.items() if k in params.keys()}
            # _args = tuple(
            #     x
            #     for i, x in enumerate(params.keys())
            #     if i < (len(params.keys()) - len(_kwargs.keys()))
            # )
            return condition(*args, **kwargs)
        return condition()


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
        self.action = action
        self.cond = cond

    def __repr__(self) -> str:
        return repr(f"Transition(event={self.event}, target={self.target})")

    @classmethod
    def create(cls, settings: Union['Transition', dict]) -> 'Transition':
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
                    else []
                ),
                cond=(
                    tuple(map(Guard.create, tuplize(settings['cond'])))
                    if 'cond' in settings
                    else []
                ),
            )
        raise InvalidConfig('could not find a valid transition configuration')

    def callback(self) -> Callable:
        """Provide callback capbility."""

        def event(machine: 'StateChart', *args: Any, **kwargs: Any) -> None:
            machine._process_transitions(self.event, *args, **kwargs)

        event.__name__ = self.event
        event.__doc__ = f"Show event: '{self.event}'."
        return event

    def evaluate(
        self, machine: 'StateChart', *args: Any, **kwargs: Any
    ) -> bool:
        """Evaluate guard conditions to determine correct transition."""
        result = True
        if self.cond:
            for cond in self.cond:
                result = cond.evaluate(machine, *args, **kwargs)
                if not result:
                    break
        return result

    def run(self, machine: 'StateChart', *args: Any, **kwargs: Any) -> None:
        """Execute actions of the transition."""
        machine._change_state(self.target)
        if self.action:
            for action in self.action:
                action.run(machine, *args, **kwargs)
            log.info("executed action event for %r", self.event)
        else:
            log.info("no action event for %r", self.event)


class State:
    """Represent state."""

    __initial: Optional['Content']
    __on_entry: Optional[Iterable[Action]]
    __on_exit: Optional[Iterable[Action]]

    def __init__(
        self,
        name: str,
        transitions: Optional[List['Transition']] = None,
        states: Optional[List['State']] = None,
        **kwargs: Any,
    ) -> None:
        if not name.replace('_', '').isalnum():
            raise InvalidConfig('state name contains invalid characters')
        self.name = name
        self.__kind = kwargs.get('kind')
        self.__initial = kwargs.get('initial')
        self.__states = {x.name: x for x in states or []}
        self.__transitions = transitions or []
        for x in self.transitions:
            self.__register_transition_callback(x)
        # FIXME: pseudostates should not include triggers
        self.__on_entry = kwargs.get('on_entry')
        self.__on_exit = kwargs.get('on_exit')
        self.__validate_state()

    def __repr__(self) -> str:
        return repr(f"State({self.name})")

    def __eq__(self, other: object) -> bool:
        if isinstance(other, State):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return False

    def __register_transition_callback(self, t: 'Transition') -> None:
        # XXX: currently mapping to class instead of instance
        # TODO: need way to provide auto-transition
        setattr(
            self,
            t.event if t.event != '' else '_auto_',
            # pylint: disable-next=unnecessary-dunder-call
            t.callback().__get__(self, self.__class__),
        )

    def __validate_state(self) -> None:
        # TODO: empty statemachine should default to null event
        if self.kind == 'compund':
            if len(self.__states) < 2:
                raise InvalidConfig('There must be at least two states')
            if not self.initial:
                raise InvalidConfig('There must exist an initial state')
        if self.kind == 'final' and self.__on_exit:
            log.warning('final state will never run "on_exit" action')
        log.info('evaluated state')

    @classmethod
    def create(cls, settings: Union['State', dict, str]) -> 'State':
        """Consolidate."""
        if isinstance(settings, cls):
            return settings
        if isinstance(settings, str):
            return cls(settings)
        if isinstance(settings, dict):
            return settings.get('factory', cls)(
                name=settings['name'],
                initial=settings.get('initial'),
                kind=settings.get('kind'),
                states=(
                    list(map(State.create, settings.pop('states')))
                    if 'states' in settings
                    else None
                ),
                transitions=(
                    list(map(Transition.create, settings['transitions']))
                    if 'transitions' in settings
                    else []
                ),
                on_entry=(
                    tuple(map(Action.create, tuplize(settings['on_entry'])))
                    if 'on_entry' in settings
                    else None
                ),
                on_exit=(
                    tuple(map(Action.create, tuplize(settings['on_exit'])))
                    if 'on_exit' in settings
                    else []
                ),
            )
        raise InvalidConfig('could not find a valid state configuration')

    @property
    def initial(self) -> Optional['Content']:
        """Return initial substate if defined."""
        return self.__initial

    @property
    def kind(self) -> str:
        """Return state type."""
        if self.__kind:
            kind = self.__kind
        elif self.substates:
            kind = 'compound'
        else:
            # FIXME: error when enterin atomic state
            # kind = 'atomic' if self.transitions else 'final'
            kind = 'atomic'
        return kind

    @property
    def substates(self) -> Dict[str, 'State']:
        """Return substates."""
        return self.__states

    @property
    def transitions(self) -> Tuple['Transition', ...]:
        """Return transitions of this state."""
        return tuple(self.__transitions)

    def get_transition(self, event: str) -> Tuple['Transition', ...]:
        """Get each transition maching event."""
        return tuple(
            filter(
                lambda transition: transition.event == event, self.transitions
            )
        )

    def _run_on_entry(self, machine: 'StateChart') -> None:
        if self.__on_entry is not None:
            for action in self.__on_entry:
                action.run(machine)
                log.info(
                    "executed 'on_entry' state change action for %s", self.name
                )

    def _run_on_exit(self, machine: 'StateChart') -> None:
        if self.__on_exit is not None:
            for action in self.__on_exit:
                action.run(machine)
                log.info(
                    "executed 'on_exit' state change action for %s", self.name
                )


class MetaStateChart(type):
    """Provide capability to populate configuration for statemachine ."""

    _root: 'State'

    def __new__(
        mcs,
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
    ) -> 'MetaStateChart':
        obj = super().__new__(mcs, name, bases, attrs)
        if '__statechart__' in attrs:
            settings = attrs.pop('__statechart__')
            obj._root = settings.pop('factory', State)(
                name=settings.pop('name', 'root'),
                initial=settings.pop('initial', None),
                kind=settings.pop('kind', None),
                states=(
                    list(map(State.create, settings.pop('states')))
                    if 'states' in settings
                    else None
                ),
                transitions=(
                    list(map(Transition.create, settings.pop('transitions')))
                    if 'transitions' in settings
                    else None
                ),
            )
        return obj


class StateChart(metaclass=MetaStateChart):
    """Provide state management capability."""

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

        if hasattr(self.__class__, '_root'):
            self.__state = self.__superstate = self.__root = deepcopy(
                self.__class__._root
            )
        else:
            raise InvalidConfig(
                'attempted initialization with empty superstate'
            )

        self.__process_initial(initial or self.superstate.initial)
        log.info('loaded states and transitions')

        if kwargs.get('enable_start_transition', True):
            self.__state._run_on_entry(self)
            self.__process_transient_state()
        log.info('statemachine initialization complete')

    def __getattr__(self, name: str) -> Any:
        if name.startswith('__'):
            raise AttributeError

        if name.startswith('is_'):
            return self.state.name == name[3:]

        # if self.state.kind == 'final':
        #     raise InvalidTransition('final state cannot transition')

        for t in self.transitions:
            if t.event == name or (t.event == '' and name == '_auto_'):
                # pylint: disable-next=unnecessary-dunder-call
                return t.callback().__get__(self, self.__class__)
        raise AttributeError(f"unable to find {name!r} attribute")

    @property
    def initial(self) -> Optional['Content']:
        """Initial state of state machine."""
        return self.superstate.initial

    @property
    def transitions(self) -> Tuple['Transition', ...]:
        """Return list of current transitions."""
        return (
            tuple(self.state.transitions)
            if hasattr(self.state, 'transitions')
            else ()
        )

    @property
    def superstate(self) -> 'State':
        """Return superstate."""
        return self.__superstate

    @property
    def states(self) -> Tuple['State', ...]:
        """Return list of states."""
        return tuple(self.superstate.substates.values())

    @property
    def state(self) -> 'State':
        """Return the current state."""
        try:
            return self.__state
        except Exception as exc:
            log.error('state is undefined')
            raise KeyError from exc

    def get_state(self, statepath: str) -> 'State':
        """Get state from query path."""
        subpaths = statepath.split('.')
        current = self.state if statepath.startswith('.') else self.__root
        for i, s in enumerate(subpaths):
            if current != s:
                current = current.substates[s]
            if i == (len(subpaths) - 1):
                log.info('found state %r', current.name)
                return current
        raise InvalidState(f"state could not be found: {statepath}")

    def _change_state(self, s: str) -> None:
        """Change current state to target state."""
        log.info('changing state from %s', s)
        # XXX: might not want target selection to be callable
        s = s(self) if callable(s) else s
        # superstate = state.split('.')[:-1]
        # self.__supertstate = (
        #     self.get_state('.'.join(superstate))
        #     if superstate != []
        #     else self.__root
        # )
        self.state._run_on_exit(self)
        self.__state = self.get_state(s)
        self.state._run_on_entry(self)
        if self.state.kind == 'compound':
            self.__superstate = self.state
            if self.state.kind == 'compound':
                self.__process_initial(self.state.initial)
        self.__process_transient_state()
        log.info('changed state to %s', s)

    def transition(
        self, event: str, statepath: Optional[str] = None
    ) -> Optional[Any]:
        """Transition from one state to another."""
        s = self.get_state(statepath) if statepath else self.state
        for t in s.transitions:
            if t.event == event:
                # pylint: disable-next=unnecessary-dunder-call
                return t.callback().__get__(self, self.__class__)
        return None

    def _process_transitions(
        self, event: str, *args: Any, **kwargs: Any
    ) -> None:
        # TODO: need to consider superstate transitions.
        txs = self.state.get_transition(event)
        # txs += self.superstate.get_transition(event)
        if txs == []:
            raise InvalidTransition('no transitions match event')
        tx = self.__evaluate_guards(txs, *args, **kwargs)
        tx.run(self, *args, **kwargs)
        log.info('processed transition event %s', tx.event)

    def __process_initial(self, initial: Optional['Content'] = None) -> None:
        if initial:
            _initial = initial(self) if callable(initial) else initial
            self.__state = self.get_state(_initial)
        else:
            raise InvalidConfig('an initial state must exist for statechart')

    def __process_transient_state(self) -> None:
        for x in self.state.transitions:
            if x.event == '':
                self._auto_()
                break

    def __evaluate_guards(
        self, txs: Tuple['Transition', ...], *args: Any, **kwargs: Any
    ) -> 'Transition':
        allowed = []
        for tx in txs:
            if tx.evaluate(self, *args, **kwargs):
                allowed.append(tx)
        if len(allowed) == 0:
            raise GuardNotSatisfied(
                'Guard is not satisfied for this transition'
            )
        if len(allowed) > 1:
            raise ForkedTransition(
                'More than one transition was allowed for this event'
            )
        log.info('processed guard for %s', allowed[0].event)
        return allowed[0]


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
