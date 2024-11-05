import asyncio
import argparse
import pandas as pd
import numpy as np
import os

from main_rps import main_async
from llm_plan.agent.rps.sequential_opponent_globals import SEQUENTIAL_OPPONENTS

async def run_experiments(agent_type, llm_type, num_seeds, num_rounds):
    # Load existing results
    per_episode_file = './results/all_models/rps_scores_per_episode.csv'
    if os.path.exists(per_episode_file):
        df_results = pd.read_csv(per_episode_file)
    else:
        df_results = pd.DataFrame()

    # Loop over each opponent type
    #for opponent_type in SEQUENTIAL_OPPONENTS:
    SEQUENTIAL_OPPONENTS = ['prev_outcome_prev_transition']
    for opponent_type in SEQUENTIAL_OPPONENTS:
        # Filter existing results for current agent and opponent
        existing_results = df_results[(df_results['tom_agent_class'] == f"{agent_type}_{llm_type}") & (df_results['sequential_agent_class'] == opponent_type)]

        existing_seeds = len(existing_results)
        seeds_needed = num_seeds - existing_seeds

        if seeds_needed > 0:
            print(f"Running {seeds_needed} seed(s) for Agent: {agent_type}, Opponent: {opponent_type}")
            for seed in range(existing_seeds, num_seeds):
                print(f"Running Seed {seed + 1}/{num_seeds} for Opponent: {opponent_type}")

                # Set random seed for reproducibility
                np.random.seed(seed)

                # Run the game
                await main_async(agent_type, llm_type, opponent_type, num_rounds=num_rounds, seed=seed)

        else:
            print(f"No additional seeds needed for Agent: {agent_type}, Opponent: {opponent_type}")

def main():
    parser = argparse.ArgumentParser(description='Run RPS experiments with specified parameters.')
    parser.add_argument('--agent_type', type=str, default='hm', help='Agent type (default: hm)')
    parser.add_argument('--llm_type', type=str, default='gpt4o', help='LLM type (default: gpt4o)')
    parser.add_argument('--num_seeds', type=int, default=3, help='Number of seeds per opponent (default: 3)')
    parser.add_argument('--num_rounds', type=int, default=300, help='Number of rounds per game (default: 300)')
    args = parser.parse_args()

    asyncio.run(run_experiments(args.agent_type, args.llm_type, args.num_seeds, args.num_rounds))

if __name__ == '__main__':
    main()