"""
Library for instantiating a sequential opponent for the matrix form rock, paper, scissors game.
"""

import numpy as np



class SequentialOpponent:
    def __init__(self, id, action_matrix=None):
        self.id = id # NB: this is only used for interpretability, not in behavior logic
        self.action_matrix = action_matrix
        # self.previous_actions = []
        # self.opponent_previous_actions = []

    def __str__(self):
        return f"Agent has type (`id`): {self.id} \
            \n-> Transition matrix (`action_matrix`): \n{self.action_matrix}"

    def get_action(self):
        pass





class SelfTransition(SequentialOpponent):
    """
    NB: all the SelfTransition class "knows" is what information to pass to its action matrix to choose its next move (its own previous move).
    When it doesn't yet have a previous move, it chooses randomly.
    If it doesn't receive an action matrix at initialization, it always chooses randomly.
    """
    def get_action(self, action_history):
        if self.action_matrix is None or len(action_history) == 0:
            # randomly choose a move by using transition probabilities over randomly selected previous move
            transition_probs = self.action_matrix.loc[np.random.choice(self.action_matrix.index.values)]
        else:
            # use last move to determine next move probabilities
            transition_probs = self.action_matrix.loc[action_history[-1]['my_last_play']]
        return np.random.choice(transition_probs.index.values, p=transition_probs.values)

