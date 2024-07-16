"""
Library for instantiating a sequential opponent for the matrix form rock, paper, scissors game.

How to use this library:

> from sequential_opponent import get_sequential_opponent
>
> def main():
>     opponent = get_sequential_opponent()
>     opponent.get_action()
>     opponent.update(opponent_action='paper')
>     print(str(opponent))


"""

import numpy as np
from sequential_opponent_globals import ACTIONS, SEQUENTIAL_OPPONENTS, ACTION_MATRIX_LOOKUP



# TODO this function will get replaced by something in main that configures the appropriate agent
def get_sequential_opponent():
    return init_sequential_opponent(np.random.choice(SEQUENTIAL_OPPONENTS))


def init_sequential_opponent(opponent_type):
    if opponent_type == 'self_transition_up':
        return SelfTransition(id=opponent_type, action_matrix=ACTION_MATRIX_LOOKUP[opponent_type])
    elif opponent_type == 'self_transition_down':
        return SelfTransition(id=opponent_type, action_matrix=ACTION_MATRIX_LOOKUP[opponent_type])
    else:
        raise ValueError(f"Unknown opponent type: {opponent_type}")



class SequentialOpponent:
    def __init__(self, id, action_matrix=None):
        self.id = id # NB: this is only used for interpretability, not in behavior logic
        self.action_matrix = action_matrix
        self.previous_actions = []
        self.opponent_previous_actions = []

    def get_action(self):
        pass

    def update(self, opponent_action):
        self.opponent_previous_actions.append(opponent_action)

    def get_state(self):
        return {
            'id': self.id,
            'action_matrix': self.action_matrix,
            'previous_actions': self.previous_actions,
            'opponent_previous_actions': self.opponent_previous_actions
        }

    def __str__(self):
        return f"Agent has type (`id`): {self.id} \
            \n-> Transition matrix (`action_matrix`): \n{self.action_matrix} \
            \n-> Previous actions (`previous_actions`): \n{self.previous_actions} \
            \n-> Opponent previous actions (`opponent_previous_actions`): \n{self.opponent_previous_actions}"



class SelfTransition(SequentialOpponent):
    """
    NB: all the SelfTransition class "knows" is what information to pass to its action matrix to choose its next move (its own previous move).
    When it doesn't yet have a previous move, it chooses randomly.
    If it doesn't receive an action matrix at initialization, it always chooses randomly.
    """
    def get_action(self):
        if self.action_matrix is None or len(self.previous_actions) == 0:
            action = np.random.choice(ACTIONS)
        else:
            transition_probs = self.action_matrix.loc[self.previous_actions[-1]]
            action = np.random.choice(transition_probs.index.values, p=transition_probs.values)
        self.previous_actions.append(action)
        return action

