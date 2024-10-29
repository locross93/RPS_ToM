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


def save_game_results(sequential_agent, tom_agent, sequential_agent_history, tom_agent_history):
    with open('game_results.csv', 'w') as csvfile:
        file = csv.writer(csvfile)
        # Write headers
        file.writerow(['sequential_agent_class', 'tom_agent_class',
                       'round_index', 'sequential_agent_move', 'tom_agent_move',
                       'sequential_agent_reward', 'tom_agent_reward'])
        # Write data
        for round_idx in range(len(sequential_agent_history)):
            file.writerow([str(sequential_agent.id), 'gpt_3.5', # TODO make this an attribute of tom_agent
                           round_idx, sequential_agent_history[round_idx]['my_last_play'], tom_agent_history[round_idx]['my_last_play'],
                           sequential_agent_history[round_idx]['reward'], tom_agent_history[round_idx]['reward']])



# NB: copied over from `running_with_scissors_in_the_matrix__repeated.py`
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


async def run_episode(tom_agent, sequential_agent, num_rounds):
    # Initialize results files
    now = datetime.datetime.now()
    date_time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    results_folder = f'./results/{tom_agent.agent_type}/{tom_agent.sequential_opponent}_{date_time_str}'
    run_label = tom_agent.agent_type+'_'+tom_agent.llm_type
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    global all_output_file
    all_output_file = os.path.join(results_folder, 'all_output_data.txt')
    with open(all_output_file, 'w') as file:
        file.write(f"{run_label}, playing rock paper scissors vs. {tom_agent.sequential_opponent}\n")
    results_file = os.path.join(results_folder, 'rps_scores.csv')
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
        # TODO how does tom_agent handle empty interaction history?
        if round_idx == 0:
            tom_agent_move = str(np.random.choice(ACTIONS))
        else:
            tom_agent_resp, tom_agent_user_msg, tom_agent_move = await tom_agent.tom_module(tom_agent_history, round_idx)
        tom_agent.interaction_num += 1

        # Calculate reward from move choices above
        sequential_agent_reward = get_reward(sequential_agent_move, tom_agent_move)
        tom_agent_reward = get_reward(tom_agent_move, sequential_agent_move)
        # Update game history
        sequential_agent_history.append({
            'round': round_idx,
            'my_last_play': sequential_agent_move,
            'opponent_last_play': tom_agent_move,
            'reward': int(sequential_agent_reward)
        })
        tom_agent_history.append({
            'round': round_idx,
            'my_play': tom_agent_move,
            'opponent_play': sequential_agent_move,
            'my_reward': int(tom_agent_reward)
        })
        df_results = df_results._append({'sequential_agent_class': str(sequential_agent.id), 'tom_agent_class': run_label,
                           'round_index': round_idx, 'sequential_agent_move': sequential_agent_move, 'tom_agent_move': tom_agent_move,
                           'sequential_agent_reward': sequential_agent_reward, 'tom_agent_reward': tom_agent_reward}, ignore_index=True)

        # Log results
        if round_idx > 0:
            print_and_save(f"User Message: {tom_agent_user_msg}")
            print_and_save(f"Response: {tom_agent_resp}")
            time_elapsed = round((datetime.datetime.now() - now).total_seconds() / 60,1)
            print_and_save(f"Time Elapsed: {time_elapsed} minutes")
            print_and_save(f"\n")
        total_cost = round(tom_agent.controller.total_inference_cost, 4)
        hm_reward = tom_agent.reward_tracker[tom_agent.agent_id]
        print_and_save(f"Round {round_idx}, Total Inference Cost: {total_cost}, HM Reward: {hm_reward}")
        print_and_save(f"Tom agent played {tom_agent_move} and received reward {tom_agent_reward}")
        print_and_save(f"Sequential agent played {sequential_agent_move} and received reward {sequential_agent_reward}")
        df_results.to_csv(results_file)

    # add column for timestamp
    df_results['timestamp'] = date_time_str
    all_results_file = './results/all_models/rps_scores_all_rounds.csv'
    if os.path.exists(all_results_file):
        df_all_results = pd.read_csv(all_results_file, index_col=0)
        df_all_results = pd.concat([df_all_results, df_results], ignore_index=True)
    else:
        df_all_results = df_results
    df_all_results.to_csv(all_results_file)



# TESTING: replace call to `run_episode` with this function to play two sequential agents against each other
def run_sequential_episode(tom_agent, sequential_agent, num_rounds):
    df_results = pd.DataFrame(columns=['sequential_agent_class', 'tom_agent_class',
                                    'round_index', 'sequential_agent_move', 'tom_agent_move',
                                    'sequential_agent_reward', 'tom_agent_reward'])
    sequential_agent_history = []
    tom_agent_history = []
    for round_idx in range(num_rounds):
        # Get move from sequential agent
        sequential_agent_move = sequential_agent.get_action(sequential_agent_history)
        tom_agent_move = tom_agent.get_action(tom_agent_history)
        # Calculate reward from move choices above
        sequential_agent_reward = get_reward(sequential_agent_move, tom_agent_move)
        tom_agent_reward = get_reward(tom_agent_move, sequential_agent_move)
        # Update game history
        sequential_agent_history.append({
            'round': round_idx,
            'my_last_play': sequential_agent_move,
            'opponent_last_play': tom_agent_move,
            'reward': int(sequential_agent_reward)
        })
        tom_agent_history.append({
            'round': round_idx,
            'my_last_play': tom_agent_move,
            'opponent_last_play': sequential_agent_move,
            'my_reward': int(tom_agent_reward)
        })
        df_results = df_results._append({'sequential_agent_class': str(sequential_agent.id), 'tom_agent_class': str(sequential_agent.id),
                           'round_index': round_idx, 'sequential_agent_move': sequential_agent_move, 'tom_agent_move': tom_agent_move,
                           'sequential_agent_reward': sequential_agent_reward, 'tom_agent_reward': tom_agent_reward}, ignore_index=True)

    print(df_results)

