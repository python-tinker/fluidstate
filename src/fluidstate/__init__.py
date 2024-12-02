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
    # cast,
)

__author__ = 'Jesse P. Johnson'
__author_email__ = 'jpj6652@gmail.com'
__title__ = 'fluidstate'
__description__ = 'Compact statechart that can be vendored.'
__version__ = '1.1.0a4'
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

EventAction = Union[Callable, str]
EventActions = Union[EventAction, Iterable[EventAction]]
GuardCondition = Union[Callable, str]
GuardConditions = Union[GuardCondition, Iterable[GuardCondition]]
InitialType = Union[Callable, str]

STATE: Optional['State'] = None
# enable_signature_truncation = False


def transition(config: Union['Transition', dict]) -> 'Transition':
    """Consolidate."""
    if isinstance(config, Transition):
        return config
    if isinstance(config, dict):
        return Transition(
            event=config['event'],
            target=config['target'],
            action=config.get('action'),
            cond=config.get('cond'),
        )
    raise InvalidConfig('could not find a valid transition configuration')


def state(config: Union['State', dict, str]) -> 'State':
    """Consolidate."""
    if isinstance(config, State):
        return config
    if isinstance(config, str):
        return State(config)
    if isinstance(config, dict):
        cls = config.get('factory', State)
        return cls(
            name=config['name'],
            initial=config.get('initial'),
            kind=config.get('kind'),
            states=(states(*config['states']) if 'states' in config else []),
            transitions=(
                transitions(*config['transitions'])
                if 'transitions' in config
                else []
            ),
            on_entry=config.get('on_entry'),
            on_exit=config.get('on_exit'),
        )
    raise InvalidConfig('could not find a valid state configuration')


def transitions(*args: Any) -> List['Transition']:
    """Consolidate."""
    return list(map(transition, args))


def states(*args: Any) -> List['State']:
    """Consolidate."""
    return list(map(state, args))


def create_machine(config: Dict[str, Any], **kwargs: Any) -> 'State':
    """Consolidate."""
    global STATE
    cls = kwargs.get('factory', State)
    _state = cls(
        name=config.get('name', 'root'),
        initial=config.get('initial'),
        kind=config.get('kind'),
        states=states(*config.get('states', [])),
        transitions=transitions(*config.get('transitions', [])),
        **kwargs,
    )
    STATE = _state
    return _state


def tuplize(value: Any) -> Tuple[Any, ...]:
    """Convert any type into a tuple."""
    # TODO: tuplize if generator
    return tuple(value) if type(value) in (list, tuple) else (value,)


class Action:
    """Encapsulate executable content."""

    def __init__(self, machine: 'StateChart') -> None:
        self.__machine = machine

    def run(
        self,
        params: EventActions,
        *args: Any,
        **kwargs: Any,
    ) -> Tuple[Any, ...]:
        """Run the action."""
        return tuple(
            self._run_action(x, *args, **kwargs) for x in tuplize(params)
        )

    def _run_action(
        self, action: EventAction, *args: Any, **kwargs: Any
    ) -> Any:
        if callable(action):
            return self.__run_with_args(
                action, self.__machine, *args, **kwargs
            )
        return self.__run_with_args(
            getattr(self.__machine, action), *args, **kwargs
        )

    @staticmethod
    def __run_with_args(action: Callable, *args: Any, **kwargs: Any) -> Any:
        signature = inspect.signature(action)
        if len(signature.parameters.keys()) != 0:
            return action(*args, **kwargs)
        return action()


class Guard:
    """Control the flow of transitions to states with conditions."""

    def __init__(self, machine: 'StateChart') -> None:
        self.__machine = machine

    def evaluate(
        self, cond: GuardConditions, *args: Any, **kwargs: Any
    ) -> bool:
        """Evaluate conditions."""
        result = True
        for x in tuplize(cond):
            result = result and self.__evaluate(x, *args, **kwargs)
            if result is False:
                break
        return result

    def __evaluate(
        self, cond: GuardCondition, *args: Any, **kwargs: Any
    ) -> bool:
        if callable(cond):
            return cond(self.__machine, *args, **kwargs)
        guard = getattr(self.__machine, cond)
        if callable(guard):
            return self.__evaluate_with_args(guard, *args, **kwargs)
        return bool(guard)

    @staticmethod
    def __evaluate_with_args(
        cond: Callable, *args: Any, **kwargs: Any
    ) -> bool:
        signature = inspect.signature(cond)
        params = dict(signature.parameters)

        if len(params.keys()) != 0:
            # _kwargs = {k: v for k, v in kwargs.items() if k in params.keys()}
            # _args = tuple(
            #     x
            #     for i, x in enumerate(params.keys())
            #     if i < (len(params.keys()) - len(_kwargs.keys()))
            # )
            return cond(*args, **kwargs)
        return cond()


class Transition:
    """Provide transition capability for transitions."""

    # event = cast(str, NameDescriptor())
    # target = cast(str, NameDescriptor())

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
        return (
            Guard(machine).evaluate(self.cond, *args, **kwargs)
            if self.cond
            else True
        )

    def run(self, machine: 'StateChart', *args: Any, **kwargs: Any) -> None:
        """Execute actions of the transition."""
        machine._change_state(self.target)
        if self.action:
            Action(machine).run(self.action, *args, **kwargs)
            log.info("executed action event for %r", self.event)
        else:
            log.info("no action event for %r", self.event)


class State:
    """Represent state."""

    __initial: Optional[InitialType]
    __on_entry: Optional[EventActions]
    __on_exit: Optional[EventActions]

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

        self.__state = self
        self.__states = {x.name: x for x in states or []}
        # self.__states = {x.name: x for x in args if isinstance(x, State)}

        self.__transitions = transitions or []
        # self.__transitions = [x for x in args if isinstance(x, Transition)]
        for x in self.transitions:
            self.__register_transition_callback(x)

        self.__initial = kwargs.get('initial')

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
        if self.initial and self.kind == 'parallel':
            raise InvalidConfig(
                'parallel state should not have an initial state'
            )
        if self.kind == 'final' and self.__on_exit:
            log.warning('final state will never run "on_exit" action')
        log.info('evaluated state')

    @property
    def initial(self) -> Optional[InitialType]:
        """Return initial substate if defined."""
        return self.__initial

    @property
    def kind(self) -> str:
        """Return state type."""
        if self.__kind:
            kind = self.__kind
        elif self.substates and self.transitions:
            for x in self.transitions:
                if x == '':
                    kind = 'transient'
                    break
            else:
                kind = 'compound'
        elif self.substates != {}:
            if not self.initial:
                kind = 'parallel'
            kind = 'compound'
        else:
            # XXX: can auto to final - if self.transitions != []: else 'final'
            kind = 'atomic'
        return kind

    @property
    def substate(self) -> 'State':
        """Current substate of this state."""
        return self.__state

    @property
    def substates(self) -> Dict[str, 'State']:
        """Return substates."""
        return self.__states

    @property
    def transitions(self) -> Tuple['Transition', ...]:
        """Return transitions of this state."""
        return tuple(self.__transitions)

    def add_state(self, s: 'State') -> None:
        """Add substate to this state."""
        self.__states[s.name] = s

    def add_transition(self, t: 'Transition') -> None:
        """Add transition to this state."""
        self.__transitions.append(t)
        self.__register_transition_callback(t)

    def get_transition(self, event: str) -> Tuple['Transition', ...]:
        """Get each transition maching event."""
        return tuple(
            filter(
                lambda transition: transition.event == event, self.transitions
            )
        )

    def _run_on_entry(self, machine: 'StateChart') -> None:
        """Run entry actions when leaving state."""
        if self.__on_entry is not None:
            Action(machine).run(self.__on_entry)
            log.info(
                "executed 'on_entry' state change action for %s", self.name
            )

    def _run_on_exit(self, machine: 'StateChart') -> None:
        """Run exit actions when leaving state."""
        if self.__on_exit is not None:
            Action(machine).run(self.__on_exit)
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
        global STATE
        obj = super().__new__(mcs, name, bases, attrs)
        if STATE:
            obj._root = STATE
        STATE = None
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

        # self.__traverse_states = kwargs.get('traverse_states', False)

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
            if self.state.kind == 'parallel':
                for s in self.states:
                    if s.name == name[3:]:
                        return True
            return self.state.name == name[3:]

        # for key in list(self.states):
        #     if key == name:
        #         return self.__items[name]

        if self.state.kind == 'final':
            raise InvalidTransition('final state cannot transition')

        for t in self.transitions:
            if t.event == name or (t.event == '' and name == '_auto_'):
                # pylint: disable-next=unnecessary-dunder-call
                return t.callback().__get__(self, self.__class__)
        raise AttributeError

    @property
    def initial(self) -> Optional[InitialType]:
        """Initial state of state machine."""
        return self.superstate.initial

    @property
    def transitions(self) -> Tuple['Transition', ...]:
        """Return list of current transitions."""
        # return self.state.transitions
        return tuple(
            self.state.transitions + self.superstate.transitions
            if self.state != self.superstate
            else self.state.transitions
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
        log.info('changing state from %s', state)
        # XXX: might not want target selection to be callable
        s = s(self) if callable(s) else s
        # superstate = state.split('.')[:-1]
        # self.__supertstate = (
        #     self.get_state('.'.join(superstate))
        #     if superstate != []
        #     else self.__root
        # )
        # if self.state.kind != 'parallel': iterate _run_on_exit()
        self.state._run_on_exit(self)
        self.__state = self.get_state(s)
        self.state._run_on_entry(self)
        if self.state.kind in ('compound', 'parallel'):
            self.__superstate = self.state
            if self.state.kind == 'compound':
                self.__process_initial(self.state.initial)
            if self.state.kind == 'parallel':
                # TODO: is this a better usecase for MP?
                for x in self.state.substates.values():
                    x._run_on_entry(self)
        self.__process_transient_state()
        log.info('changed state to %s', state)

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

    def add_state(self, s: 'State', statepath: Optional[str] = None) -> None:
        """Add state to either superstate or target state."""
        parent = self.get_state(statepath) if statepath else self.superstate
        parent.add_state(s)
        log.info('added state %s', s.name)

    def add_transition(
        self, tx: 'Transition', statepath: Optional[str] = None
    ) -> None:
        """Add transition to either superstate or target state."""
        target = self.get_state(statepath) if statepath else self.superstate
        target.add_transition(tx)
        log.info('added transition %s', tx.event)

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

    def __process_initial(self, initial: Optional[InitialType] = None) -> None:
        if initial:
            _initial = initial(self) if callable(initial) else initial
            self.__state = self.get_state(_initial)
        elif self.superstate.kind != 'parallel' and not self.initial:
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
