# The MIT License
#
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
__version__ = '1.0.0a2'
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
    source: StateTypes,
    target: StateType,
    trigger: Optional[EventTriggers] = None,
    need: Optional[EventTriggers] = None,
) -> None:
    log.info(
        f"recieved transition: {event}, {source}, {target}, {trigger}, {need}"
    )
    _transition_gatherer.append(
        {
            'event': event,
            'source': source,
            'target': target,
            'trigger': trigger,
            'need': need,
        }
    )


_state_gatherer = []


def state(
    name: str,
    before: Optional[EventTriggers] = None,
    after: Optional[EventTriggers] = None,
) -> None:
    log.info(f"recieved state: {name}, {before}, {before}")
    _state_gatherer.append({'name': name, 'before': before, 'after': after})


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

        for s in _state_gatherer:
            obj._class_states[str(s['name'])] = State(
                str(s['name']), s['before'], s['after']
            )

        for t in _transition_gatherer:
            transition = Transition(
                event=str(t['event']),
                source=[obj._class_states[s] for s in _tuplize(t['source'])],
                target=obj._class_states[str(t['target'])],
                trigger=t['trigger'],  # type: ignore
                need=t['need'],  # type: ignore
            )
            obj._class_transitions.append(transition)
            setattr(obj, str(t['event']), transition.event_method())

        _transition_gatherer = []
        _state_gatherer = []
        return obj


class StateMachine(metaclass=MetaStateMachine):
    initial_state: str
    _states: Dict[str, 'State']
    _transitions: List['Transition']

    def __new__(cls, *args: Any, **kwargs: Any) -> 'StateMachine':
        obj = super(StateMachine, cls).__new__(cls)
        obj._states = {}
        obj._transitions = []
        return obj

    def __init__(self) -> None:
        log.info('initializing statemachine')
        self.__bring_definitions_to_object_level()
        self._validate_machine_definitions()
        if callable(self.initial_state):
            self.initial_state = self.initial_state()
        self._current_state_object = self._state_by_name(self.initial_state)
        self._current_state_object.run_before(self)
        self.__create_state_callbacks()
        log.info('statemachine initialization complete')

    def __bring_definitions_to_object_level(self) -> None:
        self._states.update(self.__class__._class_states)
        self._transitions.extend(self.__class__._class_transitions)
        log.info('loaded states and transitions')

    def _validate_machine_definitions(self) -> None:
        if len(self._states) < 2:
            raise FluidstateInvalidConfig('There must be at least two states')
        if not getattr(self, 'initial_state', None):
            raise FluidstateInvalidConfig('There must exist an initial state')
        log.info('validated statemachine')

    def add_state(
        self,
        name: str,
        before: Optional[EventTriggers] = None,
        after: Optional[EventTriggers] = None,
    ) -> None:
        state = State(name, before, after)
        setattr(
            self,
            f"is_{state.name}",
            state.callback().__get__(self, self.__class__),
        )
        self._states[name] = state
        log.info(f"added state {name}")

    @property
    def current_state(self) -> str:
        return self._current_state_object.name

    def _new_state(self, state: 'State') -> None:
        self._current_state_object = state
        log.info(f"changed state to {state.name}")

    def _state_objects(self) -> List['State']:
        return list(self._states.values())

    @property
    def states(self) -> List[str]:
        return [s.name for s in self._state_objects()]

    def add_transition(
        self,
        event: str,
        source: StateTypes,
        target: StateType,
        trigger: Optional[str] = None,
        need: Optional[str] = None,
    ) -> None:
        transition = Transition(
            event,
            [self._state_by_name(s) for s in _tuplize(source)],
            self._state_by_name(target),
            trigger,
            need,
        )
        self._transitions.append(transition)
        setattr(
            self,
            event,
            transition.event_method().__get__(self, self.__class__),
        )
        log.info(f"added transition {event}")

    def _process_transitions(
        self, event_name: str, *args: Any, **kwargs: Any
    ) -> None:
        transitions = self._transitions_by_name(event_name)
        transitions = self._ensure_source_validity(transitions)
        this_transition = self._check_needs(transitions)
        this_transition.run(self, *args, **kwargs)

    def __create_state_callbacks(self) -> None:
        for state in self._state_objects():
            setattr(
                self,
                f"is_{state.name}",
                state.callback().__get__(self, self.__class__),
            )

    def _state_by_name(self, name: str) -> 'State':
        for state in self._state_objects():
            if state.name == name:
                return state
        raise FluidstateInvalidState(f"state could not be found: {name}")

    def _transitions_by_name(self, name: str) -> List['Transition']:
        return list(
            filter(
                lambda transition: transition.event == name, self._transitions
            )
        )

    def _ensure_source_validity(
        self, transitions: List['Transition']
    ) -> List['Transition']:
        valid_transitions: List['Transition'] = list(
            filter(
                lambda transition: transition.is_valid_from(
                    self._current_state_object
                ),
                transitions,
            )
        )
        if len(valid_transitions) == 0:
            raise FluidstateInvalidTransition(
                f"Cannot {transitions[0].event} from {self.current_state}"
            )
        return valid_transitions

    def _check_needs(self, transitions: List['Transition']) -> 'Transition':
        allowed_transitions = []
        for transition in transitions:
            if transition.check_need(self):
                allowed_transitions.append(transition)
        if len(allowed_transitions) == 0:
            raise FluidstateNeedNotSatisfied(
                "Need is not satisfied for this transition"
            )
        elif len(allowed_transitions) > 1:
            raise FluidstateForkedTransition(
                "More than one transition was allowed for this event"
            )
        return allowed_transitions[0]


class Transition:
    def __init__(
        self,
        event: str,
        source: Union['State', List['State']],
        target: 'State',
        trigger: Optional[EventTrigger] = None,
        need: Optional[EventTrigger] = None,
    ) -> None:
        self.event = event
        self.source = source
        self.target = target
        self.trigger = trigger
        self.need = Need(need)

    def __str__(self) -> str:
        return self.event

    def event_method(self) -> Callable:
        def generated_event(machine, *args, **kwargs):
            machine._process_transitions(self.event, *args, **kwargs)
            log.info(f"processed {self.event}")

        generated_event.__doc__ = f"event {self.event}"
        generated_event.__name__ = self.event
        return generated_event

    def is_valid_from(self, source: 'State') -> bool:
        return source in _tuplize(self.source)

    def check_need(self, machine: 'StateMachine') -> bool:
        return self.need.check(machine)

    def run(self, machine: 'StateMachine', *args: Any, **kwargs: Any) -> None:
        machine._current_state_object.run_after(machine)
        machine._new_state(self.target)
        self.target.run_before(machine)
        Trigger(machine).run(self.trigger, *args, **kwargs)
        log.info(f"executed trigger event for {self.event}")


class State:
    def __init__(
        self,
        name: str,
        before: Optional[EventTriggers] = None,
        after: Optional[EventTriggers] = None,
    ) -> None:
        self.name = name
        self.before = before
        self.after = after

    def __str__(self) -> str:
        return self.name

    def callback(self) -> Callable:
        def state_callback(self_machine):
            return self_machine.current_state == self.name

        return state_callback

    def run_before(self, machine: 'StateMachine') -> None:
        Trigger(machine).run(self.before)
        log.info(f"executed 'before' state change trigger for {self.name}")

    def run_after(self, machine: 'StateMachine') -> None:
        Trigger(machine).run(self.after)
        log.info(f"executed 'after' state change trigger for {self.name}")


class Trigger:
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

    def __try_to_run_with_args(
        self, trigger: Callable, *args: Any, **kwargs: Any
    ) -> None:
        try:
            trigger(*args, **kwargs)
        except TypeError:
            trigger()


class Need:
    def __init__(self, need: Optional[EventTrigger] = None) -> None:
        self.need = need

    def check(self, machine: 'StateMachine') -> bool:
        if self.need is None:
            return True
        items = _tuplize(self.need)
        result = True
        for item in items:
            result = result and self.__evaluate(machine, item)
        return result

    def __evaluate(self, machine: 'StateMachine', item: EventTrigger) -> bool:
        if callable(item):
            return item(machine)
        else:
            need = getattr(machine, item)
            if callable(need):
                need = need()
            return need


class FluidstateInvalidConfig(Exception):
    pass


class FluidstateInvalidTransition(Exception):
    pass


class FluidstateInvalidState(Exception):
    pass


class FluidstateNeedNotSatisfied(Exception):
    pass


class FluidstateForkedTransition(Exception):
    pass
