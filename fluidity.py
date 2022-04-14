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
"""Simple state machine that can be vendored.

metaclass implementation idea from
https://ianbicking.org/archive/more-on-python-metaprogramming.html

"""
import logging
from typing import Any, Callable, Dict, Iterable, List, Tuple, Optional, Union

logging.getLogger(__name__).addHandler(logging.NullHandler())

EventTrigger = Union[str, Callable]
EventTriggers = Union[EventTrigger, Iterable[EventTrigger]]
TransitionSource = EventTrigger
TransitionSources = Union[TransitionSource, Iterable[TransitionSource]]


def _tuplize(value: Any) -> Tuple[Any, ...]:
    return tuple(value) if type(value) in [list, tuple] else (value,)


_transition_gatherer = []


def transition(
    event: str,
    source: TransitionSources,
    target: str,
    action: Optional[EventTriggers] = None,
    guard: Optional[EventTriggers] = None,
) -> None:
    # print(
    #     'transition',
    #     type(event),
    #     f"{type(source)}: {source}",
    #     type(target),
    #     type(action),
    #     type(guard),
    # )
    _transition_gatherer.append([event, source, target, action, guard])


_state_gatherer = []


def state(
    name: str,
    start: Optional[EventTriggers] = None,
    finish: Optional[EventTriggers] = None,
) -> None:
    # print(
    #     'state',
    #     type(name),
    #     type(start),
    #     type(start),
    # )
    _state_gatherer.append([name, start, finish])


class MetaStateMachine(type):
    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        attrs: Dict[str, Any],
    ) -> 'MetaStateMachine':
        global _transition_gatherer, _state_gatherer
        Machine = super().__new__(cls, name, bases, attrs)
        Machine._class_transitions = []  # type: ignore
        Machine._class_states = {}  # type: ignore

        for s in _state_gatherer:
            Machine._add_class_state(*s)  # type: ignore

        for i in _transition_gatherer:
            Machine._add_class_transition(*i)  # type: ignore

        _transition_gatherer = []
        _state_gatherer = []

        return Machine


StateMachineBase = MetaStateMachine('StateMachineBase', (), {})


class StateMachine(StateMachineBase):  # type: ignore
    initial_state: Union[str, Callable]

    def __init__(self) -> None:
        self._bring_definitions_to_object_level()
        self._inject_into_parts()
        self._validate_machine_definitions()
        # print('states', [x for x in self.states])
        if callable(self.initial_state):
            self.initial_state = self.initial_state()
        print('state', self.initial_state, type(self.initial_state))
        self._current_state_object = self._state_by_name(self.initial_state)
        self._current_state_object.run_start(self)
        self._create_state_getters()

    def __new__(cls, *args: Any, **kwargs: Any) -> 'StateMachine':
        obj = super(StateMachine, cls).__new__(cls)
        obj._states = {}
        obj._transitions = []
        return obj

    def _bring_definitions_to_object_level(self) -> None:
        self._states.update(self.__class__._class_states)
        self._transitions.extend(self.__class__._class_transitions)

    def _inject_into_parts(self) -> None:
        for collection in [self._states.values(), self._transitions]:
            for component in collection:
                component.machine = self

    def _validate_machine_definitions(self) -> None:
        if len(self._states) < 2:
            raise InvalidConfiguration('There must be at least two states')
        if not getattr(self, 'initial_state', None):
            raise InvalidConfiguration('There must exist an initial state')

    @classmethod
    def _add_class_state(
        cls,
        name: str,
        start: Optional[EventTriggers] = None,
        finish: Optional[EventTriggers] = None,
    ) -> None:
        """Convert state into state instance.

        This is used to poplate states via metaclass.

        """
        cls._class_states[name] = State(name, start, finish)

    def add_state(
        self,
        name: str,
        start: Optional[EventTriggers] = None,
        finish: Optional[EventTriggers] = None,
    ) -> None:
        state = State(name, start, finish)
        setattr(
            self,
            state.getter_name(),
            state.getter_method().__get__(self, self.__class__),
        )
        self._states[name] = state

    @property
    def current_state(self) -> str:
        return self._current_state_object.name

    def changing_state(self, source: str, target: str) -> None:
        """Call whenever a state change is executed."""
        pass

    def _new_state(self, state: 'State') -> None:
        self.changing_state(self._current_state_object.name, state.name)
        self._current_state_object = state

    def _state_objects(self) -> List['State']:
        return list(self._states.values())

    @property
    def states(self) -> List[str]:
        return [s.name for s in self._state_objects()]

    @classmethod
    def _add_class_transition(
        cls,
        event: str,
        source: TransitionSources,
        target: str,
        action: Optional[str] = None,
        guard: Optional[str] = None,
    ) -> None:
        """Convert transition sting into transition instance.

        This is used to poplate transitions via metaclass.

        """
        transition = Transition(
            event,
            [cls._class_states[s] for s in _tuplize(source)],
            cls._class_states[target],
            action,
            guard,
        )
        cls._class_transitions.append(transition)
        setattr(cls, event, transition.event_method())

    def add_transition(
        self,
        event: str,
        source: TransitionSources,
        target: str,
        action: Optional[str] = None,
        guard: Optional[str] = None,
    ) -> None:
        transition = Transition(
            event,
            [self._state_by_name(s) for s in _tuplize(source)],
            self._state_by_name(target),
            action,
            guard,
        )
        self._transitions.append(transition)
        setattr(
            self,
            event,
            transition.event_method().__get__(self, self.__class__),
        )

    def _process_transitions(
        self, event_name: str, *args: Any, **kwargs: Any
    ) -> None:
        transitions = self._transitions_by_name(event_name)
        transitions = self._ensure_source_validity(transitions)
        this_transition = self._check_guards(transitions)
        this_transition.run(self, *args, **kwargs)

    def _create_state_getters(self) -> None:
        for state in self._state_objects():
            setattr(
                self,
                state.getter_name(),
                state.getter_method().__get__(self, self.__class__),
            )

    def _state_by_name(self, name: str) -> 'State':
        for state in self._state_objects():
            if state.name == name:
                return state
        raise InvalidState(f"state could not be found: {name}")

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
            raise InvalidTransition(
                f"Cannot {transitions[0].event} from {self.current_state}"
            )
        return valid_transitions

    def _check_guards(self, transitions: List['Transition']) -> 'Transition':
        allowed_transitions = []
        for transition in transitions:
            if transition.check_guard(self):
                allowed_transitions.append(transition)
        if len(allowed_transitions) == 0:
            raise GuardNotSatisfied(
                "Guard is not satisfied for this transition"
            )
        elif len(allowed_transitions) > 1:
            raise ForkedTransition(
                "More than one transition was allowed for this event"
            )
        return allowed_transitions[0]


class Transition:
    def __init__(
        self,
        event: str,
        source: TransitionSources,
        target: 'State',
        action: Optional[EventTrigger] = None,
        guard: Optional[EventTrigger] = None,
    ) -> None:
        self.event = event
        self.source = source
        self.target = target
        self.action = action
        self.guard = Guard(guard)

    def __str__(self) -> str:
        return self.event

    def event_method(self) -> Callable:
        def generated_event(machine, *args, **kwargs):
            these_transitions = machine._process_transitions(  # noqa
                self.event, *args, **kwargs
            )
            # TODO: add debugging here

        generated_event.__doc__ = f"event {self.event}"
        generated_event.__name__ = self.event
        return generated_event

    def is_valid_from(self, source: 'State') -> bool:
        return source in _tuplize(self.source)

    def check_guard(self, machine: 'StateMachine') -> bool:
        return self.guard.check(machine)

    def run(self, machine: 'StateMachine', *args: Any, **kwargs: Any) -> None:
        machine._current_state_object.run_finish(machine)
        machine._new_state(self.target)
        self.target.run_start(machine)
        ActionRunner(machine).run(self.action, *args, **kwargs)


class State:
    def __init__(
        self,
        name: str,
        start: Optional[EventTriggers] = None,
        finish: Optional[EventTriggers] = None,
    ) -> None:
        self.name = name
        self.start = start
        self.finish = finish

    def __str__(self) -> str:
        return self.name

    def getter_name(self) -> str:
        return f"is_{self.name}"

    def getter_method(self) -> Callable:
        def state_getter(self_machine):
            return self_machine.current_state == self.name

        return state_getter

    def run_start(self, machine: 'StateMachine') -> None:
        ActionRunner(machine).run(self.start)

    def run_finish(self, machine: 'StateMachine') -> None:
        ActionRunner(machine).run(self.finish)


class ActionRunner:
    def __init__(self, machine: 'StateMachine') -> None:
        self.machine = machine

    def run(
        self,
        action_param: Optional[EventTriggers] = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if not action_param:
            return
        action_items = _tuplize(action_param)
        for action_item in action_items:
            self._run_action(action_item, *args, **kwargs)

    def _run_action(
        self, action: EventTrigger, *args: Any, **kwargs: Any
    ) -> None:
        if callable(action):
            self._try_to_run_with_args(action, self.machine, *args, **kwargs)
        else:
            self._try_to_run_with_args(
                getattr(self.machine, action), *args, **kwargs
            )

    def _try_to_run_with_args(
        self, action: Callable, *args: Any, **kwargs: Any
    ) -> None:
        try:
            action(*args, **kwargs)
        except TypeError:
            action()


class Guard:
    def __init__(self, guard: Optional[EventTrigger] = None) -> None:
        self.guard = guard

    def check(self, machine: 'StateMachine') -> bool:
        if self.guard is None:
            return True
        items = _tuplize(self.guard)
        result = True
        for item in items:
            result = result and self._evaluate(machine, item)
        return result

    def _evaluate(
        self, machine: 'StateMachine', item: EventTrigger
    ) -> EventTrigger:
        if callable(item):
            return item(machine)
        else:
            guard = getattr(machine, item)
            if callable(guard):
                guard = guard()
            return guard


class InvalidConfiguration(Exception):
    pass


class InvalidTransition(Exception):
    pass


class InvalidState(Exception):
    pass


class GuardNotSatisfied(Exception):
    pass


class ForkedTransition(Exception):
    pass
