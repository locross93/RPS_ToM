import pandas as pd


ACTIONS = ['rock', 'paper', 'scissors'] # useful in case we modify format (e.g. 0, 1, 2)


# NB: we could standardize these by specifying the same input values for all of them, "marginalizing" differently for each type
SELF_TRANSITION_UP_ACTION_MATRIX = pd.DataFrame(
    [[0.05, 0.9, 0.05],
     [0.05, 0.05, 0.9],
     [0.9, 0.05, 0.05]],
    index=ACTIONS,
    columns=ACTIONS
)
SELF_TRANSITION_DOWN_ACTION_MATRIX = pd.DataFrame(
    [[0.05, 0.05, 0.9],
     [0.9, 0.05, 0.05],
     [0.05, 0.9, 0.05]],
    index=ACTIONS,
    columns=ACTIONS
)


SEQUENTIAL_OPPONENTS = [
    'self_transition_up',
    'self_transition_down',
    # TODO fill this in
]

ACTION_MATRIX_LOOKUP = {
    'self_transition_up': SELF_TRANSITION_UP_ACTION_MATRIX,
    'self_transition_down': SELF_TRANSITION_DOWN_ACTION_MATRIX
}