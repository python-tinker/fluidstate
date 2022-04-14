import unittest
from fluidity import StateMachine, state, transition


class ActionMachine(StateMachine):

    state(
        'created',
        entry='about_to_create',
        exit=['other_post_create', 'post_create'],
    )
    state('waiting', entry=['pre_wait', 'other_pre_wait'])
    initial_state = 'created'
    transition(source='created', event='queue', target='waiting')

    def __init__(self):
        self.entry_create = False
        super(ActionMachine, self).__init__()
        self.is_entry_aware = False
        self.is_exit_aware = False
        self.pre_wait_aware = False
        self.other_pre_wait_aware = False
        self.post_create_aware = False
        self.other_post_create_aware = False
        self.count = 0

    def pre_wait(self):
        self.is_entry_aware = True
        self.pre_wait_aware = True
        if getattr(self, 'pre_wait_expectation', None):
            self.pre_wait_expectation()

    def post_create(self):
        self.is_exit_aware = True
        self.post_create_aware = True
        if getattr(self, 'post_create_expectation', None):
            self.post_create_expectation()

    def about_to_create(self):
        self.entry_create = True

    def other_pre_wait(self):
        self.other_pre_wait_aware = True

    def other_post_create(self):
        self.other_post_create_aware = True


class FluidityAction(unittest.TestCase):
    def test_it_runs_entry_action_before_machine_entrys_a_given_state(self):
        machine = ActionMachine()
        assert machine.is_entry_aware is False
        machine.queue()
        assert machine.is_entry_aware is True

    def test_it_runs_exit_action_after_machine_exits_a_given_state(self):
        machine = ActionMachine()
        assert machine.is_exit_aware is False
        machine.queue()
        assert machine.is_entry_aware is True

    def test_it_runs_exit_action_before_entry_action(self):
        '''it runs old state's exit action before new state's entry action'''
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

    def test_it_runs_entry_action_for_initial_state_at_creation(self):
        assert ActionMachine().entry_create is True

    def test_it_accepts_many_entry_actions(self):
        machine = ActionMachine()
        assert machine.pre_wait_aware is False
        assert machine.other_pre_wait_aware is False
        machine.queue()
        assert machine.pre_wait_aware is True
        assert machine.other_pre_wait_aware is True

    def test_it_accepts_exit_actions(self):
        machine = ActionMachine()
        assert machine.post_create_aware is False
        assert machine.other_post_create_aware is False

        machine.queue()
        assert machine.post_create_aware is True
        assert machine.other_post_create_aware is True


if __name__ == '__main__':
    unittest.main()
