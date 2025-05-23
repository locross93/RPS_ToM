import asyncio
import argparse
import pandas as pd
import numpy as np
import os

from main_rps import main_async
from llm_plan.agent.rps.sequential_opponent_globals import SEQUENTIAL_OPPONENTS

async def run_experiments(agent_type, llm_type, num_seeds, num_rounds, softmax, num_hypotheses, deterministic_opponent):
    # Load existing results
    per_episode_file = './results/all_models/rps_scores_per_episode.csv'
    if os.path.exists(per_episode_file):
        df_results = pd.read_csv(per_episode_file)
    else:
        df_results = pd.DataFrame()

    # Loop over each opponent type
    SEQUENTIAL_OPPONENTS = [
        'self_transition_up',
        'self_transition_down',
        'opponent_transition_up',
        'opponent_transition_stay',
        'W_up_L_down_T_stay',
        'W_stay_L_up_T_down',
        'prev_outcome_prev_transition'
    ]
    for opponent_type in SEQUENTIAL_OPPONENTS:
        # Filter existing results for current agent, opponent, and hyperparameters
        if deterministic_opponent:
            opponent_label = f'{opponent_type}_deterministic'
        else:
            opponent_label = opponent_type
        existing_results = df_results[
            (df_results['tom_agent_class'] == f"{agent_type}_{llm_type}") &
            (df_results['sequential_agent_class'] == opponent_label ) &
            (df_results['tom_agent_softmax_temp'] == softmax) &
            (df_results['tom_agent_num_hypotheses'] == num_hypotheses)
        ]

        existing_seeds = len(existing_results)
        seeds_needed = num_seeds - existing_seeds

        if seeds_needed > 0:
            print(f"Running {seeds_needed} seed(s) for Agent: {agent_type}, Opponent: {opponent_type}")
            for seed in range(existing_seeds, num_seeds):
                print(f"Running Seed {seed + 1}/{num_seeds} for Opponent: {opponent_type}")

                # Set random seed for reproducibility
                np.random.seed(seed)

                # Run the game
                await main_async(agent_type, llm_type, opponent_type, softmax, num_hypotheses, num_rounds=num_rounds, seed=seed, deterministic_opponent=deterministic_opponent)

        else:
            print(f"No additional seeds needed for Agent: {agent_type}, Opponent: {opponent_type}")

def main():
    parser = argparse.ArgumentParser(description='Run RPS experiments with specified parameters.')
    parser.add_argument('--agent_type', type=str, default='hm', help='Agent type (default: hm)')
    parser.add_argument('--llm_type', type=str, default='gpt4o', help='LLM type (default: gpt4o)')
    parser.add_argument('--num_seeds', type=int, default=3, help='Number of seeds per opponent (default: 3)')
    parser.add_argument('--num_rounds', type=int, default=300, help='Number of rounds per game (default: 300)')
    parser.add_argument('--softmax', type=float, default=0.2, help='Softmax temperature (default: 0.2)')
    parser.add_argument('--num_hypotheses', type=int, default=5, help='Number of hypotheses to consider (default: 5)')
    parser.add_argument('--deterministic_opponent', action='store_true', default=False,
                       help='Sequential opponent chooses moves without any noise (disabled by default)')
    args = parser.parse_args()

    print(f'Running RPS experiments with parameter settings: {args}')
    asyncio.run(run_experiments(args.agent_type, args.llm_type, args.num_seeds, args.num_rounds, args.softmax, args.num_hypotheses, args.deterministic_opponent))


if __name__ == '__main__':
    main()