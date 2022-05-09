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
__description__ = 'Compact state machine that can be vendored.'
__version__ = '1.0.0b1'
__license__ = 'MIT'
__copyright__ = 'Copyright 2022 Jesse Johnson.'
__all__ = ('StateMachine', 'state', 'transition')

log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())

EventTrigger = Union[str, Callable]
EventTriggers = Union[EventTrigger, Iterable[EventTrigger]]
StateType = str
StateTypes = Union[StateType, Iterable[StateType]]


def _tuplize(value):
    return tuple(value) if type(value) in [list, tuple] else (value,)


_transition_gatherer = []


def transition(
    event: str,
    before: StateTypes,
    after: StateType,
    trigger: Optional[EventTriggers] = None,
    guard: Optional[EventTriggers] = None,
) -> None:
    log.info(f"recieved transition: {event}, {before}, {after}")
    _transition_gatherer.append(
        {
            'event': event,
            'before': before,
            'after': after,
            'trigger': trigger,
            'guard': guard,
        }
    )


_state_gatherer = []


def state(
    name: str,
    on_entry: Optional[EventTriggers] = None,
    on_exit: Optional[EventTriggers] = None,
    machine: Optional['StateMachine'] = None,
) -> None:
    log.info(f"recieved state: {name}, {on_entry}, {on_entry}")
    _state_gatherer.append(
        {
            'name': name,
            'on_entry': on_entry,
            'on_exit': on_exit,
            'machine': machine,
        }
    )


class MetaStateMachine(type):
    _class_states: Dict[str, 'State']
    _class_transitions: List['Transition']

    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
    ) -> 'MetaStateMachine':
        # if 'logging_enabled' in kwargs and kwargs.get('logging_enabled'):
        #     for handler in log.handlers[:]:
        #         log.removeHandler(handler)
        #     log.addHandler(logging.StreamHandler())

        global _transition_gatherer, _state_gatherer
        obj = super(MetaStateMachine, cls).__new__(cls, name, bases, attrs)
        obj._class_transitions = []
        obj._class_states = {}

        # TODO: create slots from here
        for s in _state_gatherer:
            obj._class_states[str(s['name'])] = State(
                name=str(s['name']),
                on_entry=s['on_entry'],
                on_exit=s['on_exit'],
                machine=s['machine'],  # type: ignore
            )

        for t in _transition_gatherer:
            transition = Transition(
                event=str(t['event']),
                before=[obj._class_states[s] for s in _tuplize(t['before'])],
                after=obj._class_states[str(t['after'])],
                trigger=t['trigger'],  # type: ignore
                guard=t['guard'],  # type: ignore
            )
            obj._class_transitions.append(transition)
            setattr(obj, str(t['event']), transition._event_callback())

        _transition_gatherer = []
        _state_gatherer = []
        return obj


class StateMachine(metaclass=MetaStateMachine):
    initial_state: str
    __states: Dict[str, 'State']
    __transitions: List['Transition']
    # NOTE: need '__dict__' to allow modification to states/transitions
    # __slots__ = ['initial_state', '__states', '__transitions', '__dict__']

    def __new__(cls, *args: Any, **kwargs: Any) -> 'StateMachine':
        obj = super(StateMachine, cls).__new__(cls)
        obj.__states = {}
        obj.__transitions = []
        return obj

    def __init__(self, initial_state: Optional[str] = None) -> None:
        log.info('initializing statemachine')
        self.__populate_instance()
        self._validate_machine()

        if initial_state:
            self.initial_state = initial_state
        elif callable(self.initial_state):
            self.initial_state = self.initial_state()

        self.__state = self._get_state(self.initial_state)
        self.__state.run_on_entry(self)
        self.__create_state_checks()
        log.info('statemachine initialization complete')

    def __getattr__(self, name: str) -> Any:
        try:
            for x in self.transitions:
                if x.event == name:
                    return x._event_callback()
            else:
                raise KeyError
        except KeyError:
            raise AttributeError

    def __populate_instance(self) -> None:
        self.__states.update(self.__class__._class_states)
        self.__transitions.extend(self.__class__._class_transitions)
        log.info('loaded states and transitions')

    def _validate_machine(self) -> None:
        # TODO: empty statemachine should default to null event
        if len(self.__states) < 2:
            raise FluidstateInvalidConfig('There must be at least two states')
        if not getattr(self, 'initial_state', None):
            raise FluidstateInvalidConfig('There must exist an initial state')
        log.info('validated statemachine')

    @property
    def transitions(self) -> List['Transition']:
        return self.__transitions

    @property
    def states(self) -> List['State']:
        return list(self.__states.values())

    @property
    def state(self) -> 'State':
        return self.__state

    def _update_state(self, state: 'State') -> None:
        self.__state = state
        log.info(f"changed state to {state.name}")

    def add_state(
        self,
        name: str,
        on_entry: Optional[EventTriggers] = None,
        on_exit: Optional[EventTriggers] = None,
        machine: Optional['StateMachine'] = None,
    ) -> None:
        state = State(name, on_entry, on_exit, machine)
        setattr(
            self,
            f"is_{state.name}",
            state.callback().__get__(self, self.__class__),
        )
        self.__states[name] = state
        log.info(f"added state {name}")

    def add_transition(
        self,
        event: str,
        before: StateTypes,
        after: StateType,
        trigger: Optional[str] = None,
        guard: Optional[str] = None,
    ) -> None:
        transition = Transition(
            event,
            [self._get_state(s) for s in _tuplize(before)],
            self._get_state(after),
            trigger,
            guard,
        )
        self.__transitions.append(transition)
        setattr(
            self,
            event,
            transition._event_callback().__get__(self, self.__class__),
        )
        log.info(f"added transition {event}")

    def _process_transitions(
        self, event_name: str, *args: Any, **kwargs: Any
    ) -> None:
        transitions = self._get_transitions(event_name)
        transitions = self._ensure_before_validity(transitions)
        this_transition = self._check_guards(transitions)
        this_transition.run(self, *args, **kwargs)

    def __create_state_checks(self) -> None:
        for state in self.states:
            setattr(
                self,
                f"is_{state.name}",
                state.callback().__get__(self, self.__class__),
            )

    def _get_state(self, name: str) -> 'State':
        for state in self.states:
            if state.name == name:
                return state
        raise FluidstateInvalidState(f"state could not be found: {name}")

    def _get_transitions(self, name: str) -> List['Transition']:
        return list(
            filter(
                lambda transition: transition.event == name, self.__transitions
            )
        )

    def _ensure_before_validity(
        self, transitions: List['Transition']
    ) -> List['Transition']:
        valid_transitions: List['Transition'] = list(
            filter(
                lambda transition: transition.validate(self.__state),
                transitions,
            )
        )
        if len(valid_transitions) == 0:
            raise FluidstateInvalidTransition(
                f"Cannot {transitions[0].event} from {self.state}"
            )
        return valid_transitions

    def _check_guards(self, transitions: List['Transition']) -> 'Transition':
        allowed_transitions = []
        for transition in transitions:
            if transition.check_guard(self):
                allowed_transitions.append(transition)
        if len(allowed_transitions) == 0:
            raise FluidstateGuardNotSatisfied(
                "Guard is not satisfied for this transition"
            )
        elif len(allowed_transitions) > 1:
            raise FluidstateForkedTransition(
                "More than one transition was allowed for this event"
            )
        # XXX: assuming duplicate transition event names are desired then
        # result should exhaust possible matching guard transitions
        return allowed_transitions[0]


class Transition:
    __slots__ = ['event', 'before', 'after', 'trigger', 'guard']

    def __init__(
        self,
        event: str,
        before: Union['State', List['State']],
        after: 'State',
        trigger: Optional[EventTrigger] = None,
        guard: Optional[EventTrigger] = None,
    ) -> None:
        self.event = event
        self.before = before
        self.after = after
        self.trigger = trigger
        self.guard = Guard(guard)

    def __repr__(self) -> str:
        return repr(
            "Transition({e}, before={s}, after={t})".format(
                e=self.event,
                s=self.before,
                t=self.after,
            )
        )

    def _event_callback(self) -> Callable:
        def event(machine, *args, **kwargs):
            machine._process_transitions(self.event, *args, **kwargs)
            log.info(f"processed {self.event}")

        event.__doc__ = f"event {self.event}"
        event.__name__ = self.event
        return event

    def validate(self, before: 'State') -> bool:
        return before in _tuplize(self.before)

    def check_guard(self, machine: 'StateMachine') -> bool:
        return self.guard.check(machine)

    def run(self, machine: 'StateMachine', *args: Any, **kwargs: Any) -> None:
        machine.state.run_on_exit(machine)
        machine._update_state(self.after)
        self.after.run_on_entry(machine)
        Trigger(machine).run(self.trigger, *args, **kwargs)
        log.info(f"executed trigger event for {self.event}")


class State:
    __slots__ = ['name', 'on_entry', 'on_exit', 'machine']

    def __init__(
        self,
        name: str,
        on_entry: Optional[EventTriggers] = None,
        on_exit: Optional[EventTriggers] = None,
        machine: Optional['StateMachine'] = None,
    ) -> None:
        self.name = name
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

    def callback(self) -> Callable:
        def state_check(machine):
            return machine.state == self.name

        return state_check

    def run_on_entry(self, machine: 'StateMachine') -> None:
        if self.on_entry is not None:
            Trigger(machine).run(self.on_entry)
            log.info(
                f"executed 'on_entry' state change trigger for {self.name}"
            )

    def run_on_exit(self, machine: 'StateMachine') -> None:
        if self.on_exit is not None:
            Trigger(machine).run(self.on_exit)
            log.info(
                f"executed 'on_exit' state change trigger for {self.name}"
            )


class Trigger:
    __slots__ = ['machine']

    def __init__(self, machine: 'StateMachine') -> None:
        self.machine = machine

    def run(
        self,
        trigger_param: Optional[EventTriggers] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if not trigger_param:
            return
        trigger_items = _tuplize(trigger_param)
        for trigger_item in trigger_items:
            self._run_trigger(trigger_item, *args, **kwargs)

    def _run_trigger(
        self, trigger: EventTrigger, *args: Any, **kwargs: Any
    ) -> None:
        if callable(trigger):
            self.__try_to_run_with_args(trigger, self.machine, *args, **kwargs)
        else:
            self.__try_to_run_with_args(
                getattr(self.machine, trigger), *args, **kwargs
            )

    @staticmethod
    def __try_to_run_with_args(
        trigger: Callable, *args: Any, **kwargs: Any
    ) -> None:
        try:
            trigger(*args, **kwargs)
        except TypeError:
            trigger()


class Guard:
    __slots__ = ['rule']

    def __init__(self, rule: Optional[EventTrigger] = None) -> None:
        self.rule = rule

    def check(self, machine: 'StateMachine') -> bool:
        if self.rule is None:
            return True
        items = _tuplize(self.rule)
        result = True
        for item in items:
            result = result and self.__evaluate(machine, item)
        return result

    @staticmethod
    def __evaluate(machine: 'StateMachine', item: EventTrigger) -> bool:
        if callable(item):
            return item(machine)
        else:
            guard = getattr(machine, item)
            if callable(guard):
                guard = guard()
            return guard


class FluidstateInvalidConfig(Exception):
    pass


class FluidstateInvalidTransition(Exception):
    pass


class FluidstateInvalidState(Exception):
    pass


class FluidstateGuardNotSatisfied(Exception):
    pass


class FluidstateForkedTransition(Exception):
    pass
