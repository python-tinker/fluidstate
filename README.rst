Fluidstate
==========

Compact state machine that can be vendored.


How to use
----------

A very simple example taken from specs::

    from fluidstate import StateMachine, state, transition

    class SimpleMachine(StateMachine):

         initial_state = 'created'

         state('created')
         state('waiting')
         state('processed')
         state('canceled')

         transition(source='created', event='queue', target='waiting')
         transition(source='waiting', event='process', target='processed')
         transition(source=['waiting', 'created'], event='cancel', target='canceled')


"A slightly more complex example"
---------------------------------

For demonstrating more advanced capabilities::

        from fluidstate import StateMachine, state, transition

        class Relationship(StateMachine):
            initial_state = (
                lambda relationship: relationship.strictly_for_fun() and 'intimate' or 'dating'
            )

            state('dating', before='make_happy', after='make_depressed')
            state('intimate', before='make_very_happy', after='never_speak_again')
            state('married', before='give_up_intimacy', after='buy_exotic_car')

            transition(source='dating', event='get_intimate', target='intimate', need='drunk')
            transition(
                source=['dating', 'intimate'],
                event='get_married',
                target='married',
                need='willing_to_give_up_manhood'
            )

            def strictly_for_fun(self) -> None: pass

            def drunk(self) -> bool: return True

            def willing_to_give_up_manhood(self) -> bool: return True

            def make_happy(self) -> None: pass

            def make_depressed(self) -> None: pass

            def make_very_happy(self) -> None: pass

            def never_speak_again(self) -> None: pass

            def give_up_intimacy(self) -> None: pass

            def buy_exotic_car(self) -> None: pass


States
------

A Fluidity state machine must have one initial state and at least one other additional state.

A state may have before and after callbacks, for running some code on state *before*
and *after*, respectively. These params can be method names (as strings),
callables, or lists of method names or callables.


Transitions
-----------

Transitions lead the machine from a state to another. Transitions must have
*source*, *target*, and *event* parameters. *source* is one or more (as list) states
from which the transition can be beforeed. *target* is the state to which the
transition will lead the machine. *event* is the method that have to be called
to launch the transition. This method is automatically created by the Fluidity
engine.

A transition can have optional *trigger* and *need* parameters. *trigger* is a
method (or callable) that will be called when transition is launched. If
parameters are passed to the event method, they are passed to the *trigger*
method, if it accepts these parameters. *need* is a method (or callable) that
is called to allow or deny the transition, depending on the result of its
execution. Both "trigger" and *need* can be lists.

The same event can be in multiple transitions, going to different states, having
their respective needs as selectors. For the transitions having the same event,
only one need should return a true value at a time.


Individuation
-------------

States and transitions are defined in a class-wide mode. However, one can define
states and transitions for individual objects. For example, having "door" as a
state machine::

    door.add_state('broken')
    door.add_transition(event='crack', source='closed', target='broken')


These additions only affect the target object.


How to install
--------------

Just run::

    pip install fluidstate


How to run tests
----------------

Just run::

    tox


Attribution
-----------

This is forked from https://github.com/nsi-iff/fluidity created by Rodrigo Manhães.
