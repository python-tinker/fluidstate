import unittest
from fluidity import StateMachine, state, transition


class ActionMachine(StateMachine):

    state(
        'created',
        start='about_to_create',
        finish=['other_post_create', 'post_create'],
    )
    state('waiting', start=['pre_wait', 'other_pre_wait'])
    initial_state = 'created'
    transition(source='created', event='queue', target='waiting')

    def __init__(self):
        self.start_create = False
        super(ActionMachine, self).__init__()
        self.is_start_aware = False
        self.is_finish_aware = False
        self.pre_wait_aware = False
        self.other_pre_wait_aware = False
        self.post_create_aware = False
        self.other_post_create_aware = False
        self.count = 0

    def pre_wait(self):
        self.is_start_aware = True
        self.pre_wait_aware = True
        if getattr(self, 'pre_wait_expectation', None):
            self.pre_wait_expectation()

    def post_create(self):
        self.is_finish_aware = True
        self.post_create_aware = True
        if getattr(self, 'post_create_expectation', None):
            self.post_create_expectation()

    def about_to_create(self):
        self.start_create = True

    def other_pre_wait(self):
        self.other_pre_wait_aware = True

    def other_post_create(self):
        self.other_post_create_aware = True


class FluidityAction(unittest.TestCase):
    def test_it_runs_start_action_before_machine_starts_a_given_state(self):
        machine = ActionMachine()
        assert machine.is_start_aware is False
        machine.queue()
        assert machine.is_start_aware is True

    def test_it_runs_finish_action_after_machine_finishs_a_given_state(self):
        machine = ActionMachine()
        assert machine.is_finish_aware is False
        machine.queue()
        assert machine.is_start_aware is True

    def test_it_runs_finish_action_before_start_action(self):
        '''it runs old state's finish action before new state's start action'''
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

    def test_it_runs_start_action_for_initial_state_at_creation(self):
        assert ActionMachine().start_create is True

    def test_it_accepts_many_start_actions(self):
        machine = ActionMachine()
        assert machine.pre_wait_aware is False
        assert machine.other_pre_wait_aware is False
        machine.queue()
        assert machine.pre_wait_aware is True
        assert machine.other_pre_wait_aware is True

    def test_it_accepts_finish_actions(self):
        machine = ActionMachine()
        assert machine.post_create_aware is False
        assert machine.other_post_create_aware is False

        machine.queue()
        assert machine.post_create_aware is True
        assert machine.other_post_create_aware is True


if __name__ == '__main__':
    unittest.main()
