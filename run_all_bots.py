import subprocess
import random
import time

# List of sequential opponents
opponents = [
    'self_transition_up',
    'self_transition_down',
    'opponent_transition_up',
    'opponent_transition_stay',
    'W_stay_L_up_T_down',
    'W_up_L_down_T_stay'
]
opponents = [
    'W_up_L_down_T_stay'
]

# Number of seeds/runs per opponent
num_seeds = 2

# LLM type
llm_type = 'llama3'

# Function to run the experiment
def run_experiment(opponent, seed):
    command = f"python main_rps.py --llm_type {llm_type} --sequential_opponent {opponent}"
    print(f"Running experiment: {command}")
    subprocess.run(command, shell=True)

# Main execution
for opponent in opponents:
    print(f"\nRunning experiments for opponent: {opponent}")
    for seed in range(num_seeds):
        print(f"\nSeed {seed + 1}/{num_seeds}")
        random.seed(seed)
        run_experiment(opponent, seed)
        # Add a short delay between runs to avoid potential API rate limiting
        time.sleep(5)

print("\nAll experiments completed.")