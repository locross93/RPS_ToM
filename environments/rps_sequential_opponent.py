"""
"""
import os
import datetime
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt


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
def print_and_save(*args, new_line=True, **kwargs):
    global all_output_file
    print(*args, **kwargs)
    with open(all_output_file, 'a') as file:
        print(*args, **kwargs, file=file)
        if new_line:
            print('\n', file=file)


def get_reward(player_move, opponent_move):
    return REWARD_LOOKUP.loc[player_move, opponent_move]


async def run_episode(tom_agent, sequential_agent, num_rounds, seed=None):
    # Initialize results files
    now = datetime.datetime.now()
    date_time_str = now.strftime("%Y-%m-%d_%H-%M-%S")
    results_folder = f'./results/{tom_agent.agent_type}/{tom_agent.sequential_opponent}_{date_time_str}'
    run_label = tom_agent.agent_type + '_' + tom_agent.llm_type
    softmax_temp = tom_agent.config['temperature'] # eb
    num_hypotheses = tom_agent.config['top_k'] # eb
    if not os.path.exists(results_folder):
        os.makedirs(results_folder)
    global all_output_file
    all_output_file = os.path.join(results_folder, 'all_output_data.txt')
    with open(all_output_file, 'w') as file:
        file.write(f"{run_label}, playing rock paper scissors vs. {tom_agent.sequential_opponent}\n")
    results_file = os.path.join(results_folder, 'rps_scores.csv')

    # Initialize game history
    df_results = pd.DataFrame(columns=['sequential_agent_class', 'tom_agent_class',
                                       'tom_agent_softmax_temp', 'tom_agent_num_hypotheses',
                                       'round_index', 'sequential_agent_move', 'tom_agent_move',
                                       'sequential_agent_reward', 'tom_agent_reward'])
    sequential_agent_history = []
    tom_agent_history = []
    for round_idx in range(num_rounds):
        # Get move from sequential agent
        sequential_agent_move = sequential_agent.get_action(sequential_agent_history)
        # Get move from tom agent
        if round_idx == 0:
            tom_agent_move = str(np.random.choice(ACTIONS))
            tom_agent_user_msg = ''
            tom_agent_resp = ''
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
        new_row = pd.DataFrame({
            'sequential_agent_class': [str(sequential_agent.id)],
            'tom_agent_class': [run_label],
            'tom_agent_softmax_temp': [softmax_temp],
            'tom_agent_num_hypotheses': [num_hypotheses],
            'round_index': [round_idx],
            'sequential_agent_move': [sequential_agent_move],
            'tom_agent_move': [tom_agent_move],
            'sequential_agent_reward': [sequential_agent_reward],
            'tom_agent_reward': [tom_agent_reward]
        })
        
        if df_results.empty:
            df_results = new_row
        else:
            df_results = pd.concat([df_results, new_row], ignore_index=True)

        # Log results
        if round_idx > 0:
            print_and_save(f"User Message: {tom_agent_user_msg}")
            print_and_save(f"Response: {tom_agent_resp}")
            time_elapsed = round((datetime.datetime.now() - now).total_seconds() / 60, 1)
            print_and_save(f"Time Elapsed: {time_elapsed} minutes")
            print_and_save(f"\n")
        total_cost = round(tom_agent.controller.total_inference_cost, 4)
        hm_reward = tom_agent.reward_tracker[tom_agent.agent_id]
        print_and_save(f"Round {round_idx}, Total Inference Cost: {total_cost}, HM Reward: {hm_reward}")
        print_and_save(f"Tom agent played {tom_agent_move} and received reward {tom_agent_reward}")
        print_and_save(f"Sequential agent played {sequential_agent_move} and received reward {sequential_agent_reward}")
        df_results.to_csv(results_file)

    # Add column for timestamp
    df_results['timestamp'] = date_time_str

    # Calculate wins, losses, and ties
    df_results['win'] = df_results['tom_agent_reward'] == 3
    df_results['loss'] = df_results['tom_agent_reward'] == -1
    df_results['tie'] = df_results['tom_agent_reward'] == 0

    total_wins = df_results['win'].sum()
    total_losses = df_results['loss'].sum()
    total_ties = df_results['tie'].sum()
    total_games = total_wins + total_losses + total_ties

    win_percentage = total_wins / total_games if total_games > 0 else 0
    loss_percentage = total_losses / total_games if total_games > 0 else 0
    tie_percentage = total_ties / total_games if total_games > 0 else 0

    df_results['win_percentage'] = win_percentage
    df_results['loss_percentage'] = loss_percentage
    df_results['tie_percentage'] = tie_percentage

    # Set seaborn style
    sns.set(style='whitegrid')

    # Data for plotting
    percentages = [win_percentage, loss_percentage, tie_percentage]
    labels = ['Win', 'Loss', 'Tie']

    # Create a DataFrame for seaborn
    plot_data = pd.DataFrame({
        'Outcome': labels,
        'Percentage': percentages
    })

    # Choose a color palette
    palette = sns.color_palette('pastel')

    # Plot using seaborn
    plt.figure(figsize=(8, 6))
    sns.barplot(x='Outcome', y='Percentage', data=plot_data, palette=palette)
    plt.ylim(0, 1)
    plt.ylabel('Percentage')
    plt.title('Game Outcome Percentages per Episode')

    # Add percentage labels above bars
    for index, row in plot_data.iterrows():
        plt.text(index, row['Percentage'] + 0.02, f"{row['Percentage']:.2%}", ha='center', fontweight='bold')

    # Save the plot
    plot_file = os.path.join(results_folder, 'game_outcome_percentages.png')
    plt.savefig(plot_file, bbox_inches='tight')
    plt.close()

    # Update the all_rounds CSV file
    # only save to all_models if 300 rounds
    if num_rounds == 300:
        all_results_file = './results/all_models/rps_scores_all_rounds.csv'
        if os.path.exists(all_results_file):
            df_all_results = pd.read_csv(all_results_file, index_col=0)
            df_all_results = pd.concat([df_all_results, df_results], ignore_index=True)
        else:
            df_all_results = df_results
        df_all_results.to_csv(all_results_file)

        # Create or update the per-episode summary CSV file
        df_episode_summary = pd.DataFrame({
            'sequential_agent_class': [str(sequential_agent.id)],
            'tom_agent_class': [run_label],
            'tom_agent_softmax_temp': [softmax_temp],
            'tom_agent_num_hypotheses': [num_hypotheses],
            'timestamp': [date_time_str],
            'seed': [seed],
            'total_wins': [total_wins],
            'total_losses': [total_losses],
            'total_ties': [total_ties],
            'win_percentage': [win_percentage],
            'loss_percentage': [loss_percentage],
            'tie_percentage': [tie_percentage],
            'total_cost': [total_cost],
            'total_time': [time_elapsed]
        })
        per_episode_file = './results/all_models/rps_scores_per_episode.csv'
        if os.path.exists(per_episode_file):
            df_all_episode_results = pd.read_csv(per_episode_file, index_col=0)
            df_all_episode_results = pd.concat([df_all_episode_results, df_episode_summary], ignore_index=True)
        else:
            df_all_episode_results = df_episode_summary
        df_all_episode_results.to_csv(per_episode_file)


