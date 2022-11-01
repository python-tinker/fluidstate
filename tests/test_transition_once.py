import pytest

from fluidstate import (
    ForkedTransition,
    StateChart,
    State,
    Transition,
    states,
    transitions,
)


class LoanRequest(StateChart):
    initial = 'pending'
    states(
        State(
            'pending',
            transitions(
                Transition(
                    event='analyze',
                    target='analyzing',
                    action='input_data',
                )
            ),
        ),
        State(
            'analyzing',
            transitions(
                Transition(
                    event='forward_analysis_result',
                    cond='was_loan_accepted',
                    target='accepted',
                ),
                Transition(
                    event='forward_analysis_result',
                    cond='was_loan_refused',
                    target='refused',
                ),
            ),
        ),
        State('refused'),
        State('accepted'),
    )

    def input_data(self, accepted=True):
        self.accepted = accepted

    def was_loan_accepted(self):
        return self.accepted or getattr(self, 'truify', False)

    def was_loan_refused(self):
        return not self.accepted or getattr(self, 'truify', False)


def test_it_selects_the_transition_having_a_passing_guard():
    request = LoanRequest()
    request.analyze()
    request.forward_analysis_result()
    request.state == 'accepted'

    request = LoanRequest()
    request.analyze(accepted=False)
    request.forward_analysis_result()
    request.state == 'refused'


def test_it_raises_error_if_more_than_one_guard_passes():
    request = LoanRequest()
    request.analyze()
    request.truify = True
    # More than one transition was allowed for this event
    with pytest.raises(ForkedTransition):
        request.forward_analysis_result()