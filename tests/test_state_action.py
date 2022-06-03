import unittest

from fluidstate import StateMachine, state, transition


class ActionMachine(StateMachine):

    state(
        'created',
        on_entry='about_to_create',
        on_exit=['other_on_exit_create', 'on_exit_create'],
    )
    state('waiting', on_entry=['pre_wait', 'other_pre_wait'])
    initial_state = 'created'
    transition(before='created', event='queue', after='waiting')

    def __init__(self):
        self.pre_create = False
        super(ActionMachine, self).__init__()
        self.is_pre_aware = False
        self.is_on_exit_aware = False
        self.pre_wait_aware = False
        self.other_pre_wait_aware = False
        self.on_exit_create_aware = False
        self.other_on_exit_create_aware = False
        self.count = 0

    def pre_wait(self):
        self.is_pre_aware = True
        self.pre_wait_aware = True
        if getattr(self, 'pre_wait_expectation', None):
            self.pre_wait_expectation()

    def on_exit_create(self):
        self.is_on_exit_aware = True
        self.on_exit_create_aware = True
        if getattr(self, 'on_exit_create_expectation', None):
            self.on_exit_create_expectation()

    def about_to_create(self):
        self.pre_create = True

    def other_pre_wait(self):
        self.other_pre_wait_aware = True

    def other_on_exit_create(self):
        self.other_on_exit_create_aware = True


class FluidstateAction(unittest.TestCase):
    def test_it_runs_pre_trigger_pre_machine_pres_a_given_state(self):
        machine = ActionMachine()
        assert machine.is_pre_aware is False
        machine.queue()
        assert machine.is_pre_aware is True

    def test_it_runs_on_exit_trigger_on_exit_machine_on_exits_a_given_state(self):
        machine = ActionMachine()
        assert machine.is_on_exit_aware is False
        machine.queue()
        assert machine.is_pre_aware is True

    def test_it_runs_on_exit_trigger_pre_pre_trigger(self):
        """it runs old state's on_exit trigger pre new state's pre trigger"""
        machine = ActionMachine()

        def on_exit_create_expectation(_self):
            _self.count += 1
            assert _self.count == 1

        def pre_wait_expectation(_self):
            _self.count += 1
            assert _self.count == 2

        machine.on_exit_create_expectation = on_exit_create_expectation.__get__(
            machine, ActionMachine
        )
        machine.pre_wait_expectation = pre_wait_expectation.__get__(
            machine, ActionMachine
        )
        machine.queue()

    def test_it_runs_pre_trigger_for_initial_state_at_creation(self):
        assert ActionMachine().pre_create is True

    def test_it_accepts_many_pre_triggers(self):
        machine = ActionMachine()
        assert machine.pre_wait_aware is False
        assert machine.other_pre_wait_aware is False
        machine.queue()
        assert machine.pre_wait_aware is True
        assert machine.other_pre_wait_aware is True

    def test_it_accepts_on_exit_triggers(self):
        machine = ActionMachine()
        assert machine.on_exit_create_aware is False
        assert machine.other_on_exit_create_aware is False

        machine.queue()
        assert machine.on_exit_create_aware is True
        assert machine.other_on_exit_create_aware is True


if __name__ == '__main__':
    unittest.main()
