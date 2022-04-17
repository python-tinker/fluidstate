import unittest
from fluidstate import StateMachine, state, transition


class ActionMachine(StateMachine):

    state(
        'created',
        before='about_to_create',
        after=['other_post_create', 'post_create'],
    )
    state('waiting', before=['pre_wait', 'other_pre_wait'])
    initial_state = 'created'
    transition(source='created', event='queue', target='waiting')

    def __init__(self):
        self.before_create = False
        super(ActionMachine, self).__init__()
        self.is_before_aware = False
        self.is_after_aware = False
        self.pre_wait_aware = False
        self.other_pre_wait_aware = False
        self.post_create_aware = False
        self.other_post_create_aware = False
        self.count = 0

    def pre_wait(self):
        self.is_before_aware = True
        self.pre_wait_aware = True
        if getattr(self, 'pre_wait_expectation', None):
            self.pre_wait_expectation()

    def post_create(self):
        self.is_after_aware = True
        self.post_create_aware = True
        if getattr(self, 'post_create_expectation', None):
            self.post_create_expectation()

    def about_to_create(self):
        self.before_create = True

    def other_pre_wait(self):
        self.other_pre_wait_aware = True

    def other_post_create(self):
        self.other_post_create_aware = True


class FluidstateAction(unittest.TestCase):
    def test_it_runs_before_trigger_before_machine_befores_a_given_state(self):
        machine = ActionMachine()
        assert machine.is_before_aware is False
        machine.queue()
        assert machine.is_before_aware is True

    def test_it_runs_after_trigger_after_machine_afters_a_given_state(self):
        machine = ActionMachine()
        assert machine.is_after_aware is False
        machine.queue()
        assert machine.is_before_aware is True

    def test_it_runs_after_trigger_before_before_trigger(self):
        """it runs old state's after trigger before new state's before trigger"""
        machine = ActionMachine()

        def post_create_expectation(_self):
            _self.count += 1
            assert _self.count == 1

        def pre_wait_expectation(_self):
            _self.count += 1
            assert _self.count == 2

        machine.post_create_expectation = post_create_expectation.__get__(
            machine, ActionMachine
        )
        machine.pre_wait_expectation = pre_wait_expectation.__get__(
            machine, ActionMachine
        )
        machine.queue()

    def test_it_runs_before_trigger_for_initial_state_at_creation(self):
        assert ActionMachine().before_create is True

    def test_it_accepts_many_before_triggers(self):
        machine = ActionMachine()
        assert machine.pre_wait_aware is False
        assert machine.other_pre_wait_aware is False
        machine.queue()
        assert machine.pre_wait_aware is True
        assert machine.other_pre_wait_aware is True

    def test_it_accepts_after_triggers(self):
        machine = ActionMachine()
        assert machine.post_create_aware is False
        assert machine.other_post_create_aware is False

        machine.queue()
        assert machine.post_create_aware is True
        assert machine.other_post_create_aware is True


if __name__ == '__main__':
    unittest.main()
