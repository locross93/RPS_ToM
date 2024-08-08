import numpy as np

from environments.rps_sequential_opponent import run_episode
from llm_plan.agent.rps.sequential_opponent_globals import ACTION_MATRIX_LOOKUP, SEQUENTIAL_OPPONENTS
from llm_plan.agent.rps.sequential_opponent import SelfTransition



def setup_sequential_agent(sequential_opponents, sequential_opponent_actions):
    # Configure a randomly selected sequential agent
    # TODO replace this with argparse / iterating over all opponents
    sequential_agent = np.random.choice(sequential_opponents)

    if sequential_agent == 'self_transition_up':
        return SelfTransition(id=sequential_agent, action_matrix=sequential_opponent_actions[sequential_agent])
    elif sequential_agent == 'self_transition_down':
        return SelfTransition(id=sequential_agent, action_matrix=sequential_opponent_actions[sequential_agent])
    else:
        raise ValueError(f"Unknown opponent type: {sequential_agent}")


def setup_tom_agent():
    pass




def main():
    # Initialize sequential agent
    sequential_agent = setup_sequential_agent(SEQUENTIAL_OPPONENTS, ACTION_MATRIX_LOOKUP)

    # Initialize tom agent
    tom_agent = setup_sequential_agent(SEQUENTIAL_OPPONENTS, ACTION_MATRIX_LOOKUP) # TESTING
    # TODO set up actual tom agent


    # Run game
    run_episode(tom_agent, sequential_agent, num_rounds=3, debug=True)



if __name__ == "__main__":
    main()