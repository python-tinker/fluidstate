from typing import Any, Callable, Dict, List, Tuple, Optional, Union


class Transition:
    def __init__(
        self,
        event: str,
        source: Union['State', List['State']],
        target: 'State',
        action,
        guard,
    ) -> None:
        self.event = event
        self.source = source
        self.target = target
        self.action = action
        self.guard = Guard(guard)

    def event_method(self):
        def generated_event(machine, *args, **kwargs):
            these_transitions = machine._process_transitions(
                self.event, *args, **kwargs
            )

        generated_event.__doc__ = 'event %s' % self.event
        generated_event.__name__ = self.event
        return generated_event

    def is_valid_from(self, source: 'State'):
        return source in _listize(self.source)

    def check_guard(self, machine: 'StateMachine'):
        return self.guard.check(machine)

    def run(self, machine: 'StateMachine', *args: Any, **kwargs: Any):
        machine._current_state_object.run_exit(machine)
        machine._new_state(self.target)
        self.target.run_entry(machine)
        ActionRunner(machine).run(self.action, *args, **kwargs)


class Guard:
    def __init__(self, action) -> None:
        self.action = action

    def check(self, machine: 'StateMachine'):
        if self.action is None:
            return True
        items = _listize(self.action)
        result = True
        for item in items:
            result = result and self._evaluate(machine, item)
        return result

    def _evaluate(self, machine: 'StateMachine', item: Union[Callable, str]):
        if callable(item):
            return item(machine)
        else:
            guard = getattr(machine, item)
            if callable(guard):
                guard = guard()
            return guard


class State:
    def __init__(
        self,
        name: str,
        entry,
        exit,
    ) -> None:
        self.name = name
        self.entry = entry
        self.exit = exit

    def getter_name(self) -> str:
        return 'is_%s' % self.name

    def getter_method(self) -> Callable:
        def state_getter(self_machine):
            return self_machine.current_state == self.name

        return state_getter

    def run_entry(self, machine: 'StateMachine') -> None:
        if self.entry:
            ActionRunner(machine).run(self.entry)

    def run_exit(self, machine: 'StateMachine') -> None:
        if self.exit:
            ActionRunner(machine).run(self.exit)


class ActionRunner:
    def __init__(self, machine: 'StateMachine') -> None:
        self.machine = machine

    def run(
        self,
        action_param: Optional[Union[str, List[str]]],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        if not action_param:
            return
        action_items = _listize(action_param)
        for action_item in action_items:
            self._run_action(action_item, *args, **kwargs)

    def _run_action(
        self, action: Union[Callable, str], *args: Any, **kwargs: Any
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


def _listize(value):
    return type(value) in [list, tuple] and value or [value]


# metaclass implementation idea from
# https://ianbicking.org/archive/more-on-python-metaprogramming.html
_transition_gatherer = []


def transition(
    event: str,
    source: str,
    target: str,
    action=None,
    guard=None,
) -> None:
    # XXX: action/guard are not reliable
    _transition_gatherer.append([event, source, target, action, guard])


_state_gatherer = []


def state(
    name: str,
    entry=None,
    exit=None,
) -> None:
    _state_gatherer.append([name, entry, exit])


class MetaStateMachine(type):
    def __new__(
        cls,
        name: str,
        bases: Tuple[type, ...],
        dictionary: Dict[str, Any],
    ) -> 'StateMachine':
        global _transition_gatherer, _state_gatherer
        Machine = super(MetaStateMachine, cls).__new__(  # type: ignore
            cls, name, bases, dictionary
        )
        Machine._class_transitions = []
        Machine._class_states = {}

        for s in _state_gatherer:
            Machine._add_class_state(*s)

        for i in _transition_gatherer:
            Machine._add_class_transition(*i)

        _transition_gatherer = []
        _state_gatherer = []

        return Machine


StateMachineBase = MetaStateMachine('StateMachineBase', (object,), {})


class StateMachine(StateMachineBase):  # type: ignore
    initial_state: Union[str, Callable]

    def __init__(self) -> None:
        self._bring_definitions_to_object_level()
        self._inject_into_parts()
        self._validate_machine_definitions()
        print('states', [x for x in self.states()])
        if callable(self.initial_state):
            self.initial_state = self.initial_state()
        self._current_state_object = self._state_by_name(self.initial_state)
        self._current_state_object.run_entry(self)
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
        entry=None,
        exit=None,
    ) -> None:
        cls._class_states[name] = State(name, entry, exit)

    def add_state(
        self,
        name: str,
        entry=None,
        exit=None,
    ) -> None:
        state = State(name, entry, exit)
        setattr(
            self,
            state.getter_name(),
            state.getter_method().__get__(self, self.__class__),
        )
        self._states[name] = state

    def _current_state_name(self) -> str:
        return self._current_state_object.name

    current_state = property(_current_state_name)

    def changing_state(self, source: str, target: str) -> None:
        """Call whenever a state change is executed."""
        pass

    def _new_state(self, state: 'State') -> None:
        self.changing_state(self._current_state_object.name, state.name)
        self._current_state_object = state

    def _state_objects(self) -> List['State']:
        return list(self._states.values())

    def states(self) -> List['State']:
        return [s.name for s in self._state_objects()]

    @classmethod
    def _add_class_transition(
        cls,
        event: str,
        source: str,
        target: str,
        action,
        guard,
    ) -> None:
        print('add', action, guard)
        transition = Transition(
            event,
            [cls._class_states[s] for s in _listize(source)],
            cls._class_states[target],
            action,
            guard,
        )
        cls._class_transitions.append(transition)
        setattr(cls, event, transition.event_method())

    def add_transition(
        self,
        event: str,
        source: str,
        target: str,
        action=None,
        guard=None,
    ):
        # XXX action and guard are way to ambigious:
        # Optional[Union[List[Callable[[str], Any]]]]
        transition = Transition(
            event,
            [self._state_by_name(s) for s in _listize(source)],
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
        transitions = self._ensure_sourcevalidity(transitions)
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

    def _ensure_sourcevalidity(
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
                "Cannot %s from %s"
                % (transitions[0].event, self.current_state)
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
