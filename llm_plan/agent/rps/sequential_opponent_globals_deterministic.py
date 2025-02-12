import pandas as pd


ACTIONS = ['rock', 'paper', 'scissors'] # useful in case we modify format (e.g. 0, 1, 2)


TRANSITION_UP_ACTION_MATRIX = pd.DataFrame(
    [[0.0, 1.0, 0.0],
     [0.0, 0.0, 1.0],
     [1.0, 0.0, 0.0]],
    index=ACTIONS,
    columns=ACTIONS
)
TRANSITION_DOWN_ACTION_MATRIX = pd.DataFrame(
    [[0.0, 0.0, 1.0],
     [1.0, 0.0, 0.0],
     [0.0, 1.0, 0.0]],
    index=ACTIONS,
    columns=ACTIONS
)
TRANSITION_STAY_ACTION_MATRIX = pd.DataFrame(
    [[1.0, 0.0, 0.0],
     [0.0, 1.0, 0.0],
     [0.0, 0.0, 1.0]],
    index=ACTIONS,
    columns=ACTIONS
)

OUTCOME_TRANSITION_W_stay_L_up_T_down_ACTION_MATRIX = pd.DataFrame(
    [
        # opponent's last move was 'rock'
        [pd.DataFrame(
            [[0.0, 0.0, 1.0],  # player's last move: rock
             [0.0, 1.0, 0.0],  # player's last move: paper
             [1.0, 0.0, 0.0]], # player's last move: scissors
             index=ACTIONS, # player's last move
             columns=ACTIONS # next move
        )],
        # opponent's last move was 'paper'
        [pd.DataFrame(
            [[0.0, 1.0, 0.0],  # player's last move: rock
             [1.0, 0.0, 0.0],  # player's last move: paper
             [0.0, 0.0, 1.0]], # player's last move: scissors
             index=ACTIONS, # player's last move
             columns=ACTIONS # next move
        )],
        # opponent's last move was 'scissors'
        [pd.DataFrame(
            [[1.0, 0.0, 0.0],  # player's last move: rock
             [0.0, 0.0, 1.0],  # player's last move: paper
             [0.0, 1.0, 0.0]], # player's last move: scissors
             index=ACTIONS, # player's last move
             columns=ACTIONS # next move
        )]
    ],
    index=ACTIONS # opponent's last move
)

OUTCOME_TRANSITION_W_up_L_down_T_stay_ACTION_MATRIX = pd.DataFrame(
    [
        # opponent's last move was 'rock'
        [pd.DataFrame(
            [[1.0, 0.0, 0.0],  # player's last move: rock
             [0.0, 0.0, 1.0],  # player's last move: paper
             [0.0, 1.0, 0.0]], # player's last move: scissors
             index=ACTIONS, # player's last move
             columns=ACTIONS # next move
        )],
        # opponent's last move was 'paper'
        [pd.DataFrame(
            [[0.0, 0.0, 1.0],  # player's last move: rock
             [0.0, 1.0, 0.0],  # player's last move: paper
             [1.0, 0.0, 0.0]], # player's last move: scissors
             index=ACTIONS, # player's last move
             columns=ACTIONS # next move
        )],
        # opponent's last move was 'scissors'
        [pd.DataFrame(
            [[0.0, 1.0, 0.0],  # player's last move: rock
             [1.0, 0.0, 0.0],  # player's last move: paper
             [0.0, 0.0, 1.0]], # player's last move: scissors
             index=ACTIONS, # player's last move
             columns=ACTIONS # next move
        )]
    ],
    index=ACTIONS # opponent's last move
)

# player's move two moves prior was 'rock'
PREV_OUTCOME_PREV_TRANSITION_R = pd.DataFrame(
    [
        # player's last move was 'rock'
        [pd.DataFrame(
            [[0.0, 1.0, 0.0],  # opponent's last move: rock
             [0.0, 0.0, 1.0],  # opponent's last move: paper
             [1.0, 0.0, 0.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )],
        # player's last move was 'paper'
        [pd.DataFrame(
            [[0.0, 0.0, 1.0],  # opponent's last move: rock
             [1.0, 0.0, 0.0],  # opponent's last move: paper
             [0.0, 1.0, 0.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )],
        # player's last move was 'scissors'
        [pd.DataFrame(
            [[1.0, 0.0, 0.0],  # opponent's last move: rock
             [0.0, 1.0, 0.0],  # opponent's last move: paper
             [0.0, 0.0, 1.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )]
    ],
    index=ACTIONS # player's last move
)

# player's move two moves prior was 'paper'
PREV_OUTCOME_PREV_TRANSITION_P = pd.DataFrame(
    [
        # player's last move was 'rock'
        [pd.DataFrame(
            [[1.0, 0.0, 0.0],  # opponent's last move: rock
             [0.0, 1.0, 0.0],  # opponent's last move: paper
             [0.0, 0.0, 1.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )],
        # player's last move was 'paper'
        [pd.DataFrame(
            [[0.0, 1.0, 0.0],  # opponent's last move: rock
             [0.0, 0.0, 1.0],  # opponent's last move: paper
             [1.0, 0.0, 0.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )],
        # player's last move was 'scissors'
        [pd.DataFrame(
            [[0.0, 0.0, 1.0],  # opponent's last move: rock
             [1.0, 0.0, 0.0],  # opponent's last move: paper
             [0.0, 1.0, 0.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )]
    ],
    index=ACTIONS # player's last move
)

# player's move two moves prior was 'scissors'
PREV_OUTCOME_PREV_TRANSITION_S = pd.DataFrame(
    [
        # player's last move was 'rock'
        [pd.DataFrame(
            [[0.0, 0.0, 1.0],  # opponent's last move: rock
             [1.0, 0.0, 0.0],  # opponent's last move: paper
             [0.0, 1.0, 0.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )],
        # player's last move was 'paper'
        [pd.DataFrame(
            [[1.0, 0.0, 0.0],  # opponent's last move: rock
             [0.0, 1.0, 0.0],  # opponent's last move: paper
             [0.0, 0.0, 1.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )],
        # player's last move was 'scissors'
        [pd.DataFrame(
            [[0.0, 1.0, 0.0],  # opponent's last move: rock
             [0.0, 0.0, 1.0],  # opponent's last move: paper
             [1.0, 0.0, 0.0]], # opponent's last move: scissors
             index=ACTIONS, # opponent's last move
             columns=ACTIONS # next move
        )]
    ],
    index=ACTIONS # player's last move
)

PREV_OUTCOME_PREV_TRANSITION = pd.DataFrame(
    [[PREV_OUTCOME_PREV_TRANSITION_R],
     [PREV_OUTCOME_PREV_TRANSITION_P],
     [PREV_OUTCOME_PREV_TRANSITION_S]],
    index=ACTIONS
)


SEQUENTIAL_OPPONENTS = [
    # transition opponents
    'self_transition_up',
    'self_transition_down',
    'opponent_transition_up',
    'opponent_transition_stay',
    # win-stay, lose-shift variants
    'W_stay_L_up_T_down',
    'W_up_L_down_T_stay',
    # previous outcome, previous transition
    'prev_outcome_prev_transition'
]

ACTION_MATRIX_LOOKUP_DETERMINISTIC = {
    'self_transition_up': TRANSITION_UP_ACTION_MATRIX,
    'self_transition_down': TRANSITION_DOWN_ACTION_MATRIX,
    'opponent_transition_up': TRANSITION_UP_ACTION_MATRIX,
    'opponent_transition_stay': TRANSITION_STAY_ACTION_MATRIX,
    'W_stay_L_up_T_down': OUTCOME_TRANSITION_W_stay_L_up_T_down_ACTION_MATRIX,
    'W_up_L_down_T_stay': OUTCOME_TRANSITION_W_up_L_down_T_stay_ACTION_MATRIX,
    'prev_outcome_prev_transition': PREV_OUTCOME_PREV_TRANSITION
}