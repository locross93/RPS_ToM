"""
"""
import os
import datetime
import numpy as np
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


def save_game_results(sequential_agent, tom_agent, sequential_agent_history, tom_agent_history):
    with open('game_results.csv', 'w') as csvfile:
        file = csv.writer(csvfile)
        # Write headers
        file.writerow(['sequential_agent_class', 'tom_agent_class',
                       'round_index', 'sequential_agent_move', 'tom_agent_move',
                       'sequential_agent_reward', 'tom_agent_reward'])
        # Write data
        for round_idx in range(len(sequential_agent_history)):
            file.writerow([str(sequential_agent.id), 'gpt3.5', # TODO make this an attribute of tom_agent
                           round_idx, sequential_agent_history[round_idx]['my_last_play'], tom_agent_history[round_idx]['my_last_play'],
                           sequential_agent_history[round_idx]['reward'], tom_agent_history[round_idx]['reward']])


def get_reward(player_move, opponent_move):
    return REWARD_LOOKUP.loc[player_move, opponent_move]


async def run_episode(tom_agent, sequential_agent, num_rounds, debug=False): # TODO make sense to pass in # rounds?
    # Initialize results files
    now = datetime.datetime.now()
    date_time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    agent_label = 'hm_gpt3_5'
    tom_agent.llm_type = 'gpt3.5'
    results_folder = f'./results/agent_{agent_label}_{date_time_str}'
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    global all_output_file
    all_output_file = os.path.join(results_folder, 'all_output_data.txt')
    with open(all_output_file, 'w') as file:
        file.write(f"{agent_label}, playing rock paper scissors \n\n")
    # Initialize game history
    df_results = pd.DataFrame(columns=['sequential_agent_class', 'tom_agent_class',
                                    'round_index', 'sequential_agent_move', 'tom_agent_move',
                                    'sequential_agent_reward', 'tom_agent_reward'])
    sequential_agent_history = []
    tom_agent_history = []
    for round_idx in range(num_rounds):
        # Get move from sequential agent
        sequential_agent_move = sequential_agent.get_action(sequential_agent_history)
        # Get move from tom agent
        # if debug: # TESTING
        #     tom_agent_move = tom_agent.get_action(tom_agent_history)
        # TODO how does tom_agent handle empty interaction history?
        if round_idx == 0:
            tom_agent_move = str(np.random.choice(ACTIONS))
        else:
            tom_agent_resp, tom_agent_user_msg, tom_agent_move = await tom_agent.tom_module(tom_agent_history, round_idx)

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
        df_results._append({'sequential_agent_class': str(sequential_agent.id), 'tom_agent_class': str(tom_agent.llm_type),
                           'round_index': round_idx, 'sequential_agent_move': sequential_agent_move, 'tom_agent_move': tom_agent_move,
                           'sequential_agent_reward': sequential_agent_reward, 'tom_agent_reward': tom_agent_reward}, ignore_index=True)

        # Log results
        print_and_save(f"Round {round_idx}")
        if round_idx > 0:
            print_and_save(f"User Message: {tom_agent_user_msg}")
            print_and_save(f"Response: {tom_agent_resp}")
            print_and_save(f"\n")
        print_and_save(f"Tom agent played {tom_agent_move}")
        print_and_save(f"Sequential agent played {sequential_agent_move}")

    results_file = os.path.join(results_folder, 'rps_scores.csv')
    df_results.to_csv(results_file)

    # TESTING
    print(str(sequential_agent))
    if debug:
        print(str(tom_agent))

    print(sequential_agent_history)
    print(tom_agent_history)


