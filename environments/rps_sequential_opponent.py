"""
"""

import pandas as pd


# TODO put these somewhere else?
ACTIONS = ['rock', 'paper', 'scissors'] # useful in case we modify format (e.g. 0, 1, 2)
REWARD_LOOKUP = pd.DataFrame(
    [[0, -1, 3],
     [3, 0, -1],
     [-1, 3, 0]],
    index=ACTIONS,
    columns=ACTIONS
)


# NB: copied over from `running_with_scissors_in_the_matrix__repeated.py`
# TODO do we need this?
def print_and_save(*args, new_line=True, **kwargs):
    global all_output_file
    print(*args, **kwargs)
    with open(all_output_file, 'a') as file:
        print(*args, **kwargs, file=file)
        if new_line:
            print('\n', file=file)



def get_reward(player_move, opponent_move):
    return REWARD_LOOKUP.loc[player_move, opponent_move]


async def run_episode(tom_agent, sequential_agent, num_rounds, debug=False): # TODO make sense to pass in # rounds?
    # Initialize game history
    sequential_agent_history = []
    tom_agent_history = []
    for round_idx in range(num_rounds):
        # Get move from sequential agent
        sequential_agent_move = sequential_agent.get_action(sequential_agent_history)
        # Get move from tom agent
        if debug: # TESTING
            tom_agent_move = tom_agent.get_action(tom_agent_history)
        # TODO how does tom_agent handle empty interaction history?
        tom_agent_resp, tom_agent_user_msg, tom_agent_move = await tom_agent.tom_module(tom_agent_history)
        # print_and_save(...)

        # Calculate reward from move choices above
        sequential_agent_reward = get_reward(sequential_agent_move, tom_agent_move)
        tom_agent_reward = get_reward(tom_agent_move, sequential_agent_move)
        # Update game history
        sequential_agent_history.append({
            'my_last_play': sequential_agent_move,
            'opponent_last_play': tom_agent_move,
            'reward': sequential_agent_reward
        })
        tom_agent_history.append({
            'my_last_play': tom_agent_move,
            'opponent_last_play': sequential_agent_move,
            'reward': tom_agent_reward
        })

        # Log results




    # TESTING
    print(str(sequential_agent))
    if debug:
        print(str(tom_agent))

    print(sequential_agent_history)
    print(tom_agent_history)


