import re
import ast

def extract_last_round_hypothesis(log_text):
    # Find the last round (299) interaction
    last_round_match = re.search(r"An interaction with the other player has occurred at round 299,.*?You previously guessed that their policy or strategy is: (\{.*?\}).", log_text, re.DOTALL)
    
    if not last_round_match:
        return None, None, False  # No last round hypothesis found
    
    hypothesis_str = last_round_match.group(1)
    
    try:
        hypothesis_dict = ast.literal_eval(hypothesis_str)
    except (SyntaxError, ValueError):
        # If parsing fails, try to extract just the strategy
        strategy_match = re.search(r"'Opponent_strategy': '(.*?)'", hypothesis_str)
        if strategy_match:
            return strategy_match.group(1), 0.0, False
        else:
            return None, None, False

    strategy = hypothesis_dict.get('Opponent_strategy', '')
    
    # Check if it's a good hypothesis
    is_good_hypothesis = "Good hypothesis found" in log_text.split("round 299,")[-1]
    
    # Extract value if it's a good hypothesis, otherwise set to 0
    if is_good_hypothesis:
        value = round(hypothesis_dict.get('value', 0.0), 3)
    else:
        value = 0.0
        
    breakpoint()
    
    return strategy, value, is_good_hypothesis

# File path
log_text_file = '/Users/locro/Documents/Stanford/RPS_ToM/results/agent_hm_gpt4o_2024-08-26_11-37-09/all_output_data.txt'
#log_text_file = '/Users/locro/Documents/Stanford/RPS_ToM/results/agent_hm_gpt4o_2024-08-26_12-21-12/all_output_data.txt'
with open(log_text_file, 'r') as file:
    log_text = file.read()
strategy, value, is_good_hypothesis = extract_last_round_hypothesis(log_text)
if strategy is not None:
    print(f"Strategy: {strategy}")
    print(f"Value: {value}")
    print(f"Is Good Hypothesis: {is_good_hypothesis}")
else:
    print("No hypothesis found for the last round")