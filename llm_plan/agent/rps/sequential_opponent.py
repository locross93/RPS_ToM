"""
Library for instantiating a sequential opponent for the matrix form rock, paper, scissors game.
"""

import numpy as np



class SequentialOpponent:
    def __init__(self, id, action_matrix=None):
        self.id = id # NB: this is only used for interpretability, not in behavior logic
        self.action_matrix = action_matrix

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


class OppTransition(SequentialOpponent):
    """
    Same as SelfTransition, but uses the opponent's last move to determine its next move.
    """
    def get_action(self, action_history):
        if self.action_matrix is None or len(action_history) == 0:
            # randomly choose a move by using transition probabilities over randomly selected previous move
            transition_probs = self.action_matrix.loc[np.random.choice(self.action_matrix.index.values)]
        else:
            # use opponent's last move to determine next move probabilities
            transition_probs = self.action_matrix.loc[action_history[-1]['opponent_last_play']]
        return np.random.choice(transition_probs.index.values, p=transition_probs.values)


class OutcomeTransition(SequentialOpponent):
    """
    Uses the combination of both player's last move to determine the next move.
    """
    def get_action(self, action_history):
        if self.action_matrix is None or len(action_history) == 0:
            # randomly choose a move by using transition probabilities over randomly selected previous moves by each player
            transition_matrix = self.action_matrix.loc[np.random.choice(self.action_matrix.index), 0]
            transition_probs = transition_matrix.loc[np.random.choice(transition_matrix.index)]
        else:
            # use combination of player's last move and opponent's last move to determine next move probabilities
            transition_matrix = self.action_matrix.loc[action_history[-1]['opponent_last_play'], 0]
            transition_probs = transition_matrix.loc[action_history[-1]['my_last_play']]

        return np.random.choice(transition_probs.index.values, p=transition_probs.values)

class PrevTransitionOutcomeTransition(SequentialOpponent):
    """
    Uses the combination of both player's last move, as well as the player's move two moves prior, to determine the next move.
    """
    def get_action(self, action_history):
        if self.action_matrix is None or len(action_history) < 2: # NB: need at least two moves to determine next move
            # randomly choose a move by using transition probabilities over randomly selected previous moves by each player
            # and randomly selected player move two moves prior
            outcome_transition_matrix = self.action_matrix.loc[np.random.choice(self.action_matrix.index), 0] # randomly selected two moves prior
            transition_matrix = outcome_transition_matrix.loc[np.random.choice(outcome_transition_matrix.index), 0] # randomly selected previous move
            transition_probs = transition_matrix.loc[np.random.choice(transition_matrix.index)] # randomly selected opponent previous move
        else:
            # use combination of player's last move and opponent's last move, and player's move two moves prior
            # to determine next move probabilities
            outcome_transition_matrix = self.action_matrix.loc[action_history[-2]['my_last_play'], 0] # player move two moves prior
            transition_matrix = outcome_transition_matrix.loc[action_history[-1]['my_last_play'], 0] # player previous move
            transition_probs = transition_matrix.loc[action_history[-1]['opponent_last_play']] # opponent previous move

        return np.random.choice(transition_probs.index.values, p=transition_probs.values)
