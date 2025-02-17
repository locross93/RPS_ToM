import re
import abc
import ast
import asyncio
from copy import deepcopy
import numpy as np
from queue import Queue
from typing import List, Dict, Any, Tuple, Optional

from llm_plan.agent import action_funcs

class DecentralizedAgent:
    def __init__(self, config: Dict[str, Any], controller: Any) -> None:
        self.agent_id = config['agent_id']
        self.config = config
        self.controller = controller        
        self.all_actions = Queue()
        self.generate_system_message()
        self.interact_steps = 0
        self.interaction_history = []
        self.interaction_num = 0
        self.reward_tracker = {self.agent_id: 0}
        self.n = config['n']
        self.good_hypothesis_found = False
        self.alpha = 0.3 # learning rate for updating hypothesis values
        self.correct_guess_reward = 1
        self.good_hypothesis_thr = 0.7
        self.top_k = config.get('top_k', 5)
        
        # Define the fixed set of possible strategies
        win_outcome = "win"
        tie_outcome = "tie"
        loss_outcome = "loss"
        up_transition = "plays the move that would beat their last rounds move"
        down_transition = "plays the move that would lose to their last rounds move"
        stay_transition = "plays the same move as they did in the last round"
        opponent_up_transition = "plays the move that would beat their opponents last rounds move"
        opponent_stay_transition = "plays the same move as their opponents last rounds move"

        prev_up_transition = "played the move in the last round that would beat the opponent's move two rounds ago"
        prev_down_transition = "played the move in the last round that would lose to the opponent's move two rounds ago"
        prev_stay_transition = "played the same move in the last round as the opponent played two rounds ago"

        self.possible_strategies = {
            'self_transition_up': {f'The opponent {up_transition}': 1.0},
            'self_transition_down': {f'The opponent {down_transition}': 1.0},
            'opponent_transition_up': {f'The opponent {opponent_up_transition}': 1.0},
            'opponent_transition_stay': {f'The opponent {opponent_stay_transition}': 1.0},
            'W_stay_L_up_T_down': {f'After a {win_outcome} the opponent {stay_transition}. After a {loss_outcome} the opponent {up_transition}. After a {tie_outcome} the opponent {down_transition}': 1.0},
            'W_up_L_down_T_stay': {f'After a {win_outcome} the opponent {up_transition}. After a {loss_outcome} the opponent {down_transition}. After a {tie_outcome} the opponent {stay_transition}': 1.0},
            'prev_outcome_prev_transition': {f'The opponents transition from one round to the next depends on both the previous outcome (win, lose, or tie) and the previous transition the opponent made. \
            After a {win_outcome} in which the opponent {prev_up_transition}, the opponent {up_transition}.\
            After a {win_outcome} in which the opponent {prev_down_transition}, the opponent {down_transition}. \
            After a {win_outcome} in which the opponent {prev_stay_transition}, the opponent {stay_transition}. \
            After a {loss_outcome} in which the opponent {prev_up_transition}, the opponent {stay_transition}.\
            After a {loss_outcome} in which the opponent {prev_down_transition}, the opponent {up_transition}. \
            After a {loss_outcome} in which the opponent {prev_stay_transition}, the opponent {down_transition}. \
            After a {tie_outcome} in which the opponent {prev_up_transition}, the opponent {down_transition}.\
            After a {tie_outcome} in which the opponent {prev_down_transition}, the opponent {stay_transition}. \
            After a {tie_outcome} in which the opponent {prev_stay_transition}, the opponent {up_transition}.': 1.0}
        }

    def generate_system_message(self):
        self.system_message = f"""
            You are Agent {self.agent_id} in the two player iterated game of rock paper scissors
            Rock beats scissors, paper beats rock, and scissors beats paper.
            Winner gets 3 reward, loser gets -1 reward, and tie gives 0 reward.
            You will be playing the same opponent for 300 rounds.
            """

    def generate_strategy_selection_message(self, step):
        #strategies_str = "\n".join([f"{k}: {v}" for k, v in self.possible_strategies.items()])
        strategies_str = "\n".join([f"{v}" for k, v in self.possible_strategies.items()])
        
        user_message = f"""
            An interaction with the other player has occurred at round {step}, {self.interaction_history[-1]}.
            The total interaction history is: {self.interaction_history}.

            Above is the history of interactions. Below are the possible strategies your opponent could be using:
            {strategies_str}

            Think step by step about which strategy best explains your opponent's behavior so far.
            Consider:
            1. Are there patterns in how they respond to your moves?
            2. Does their behavior change based on wins, losses, or ties?
            3. Which strategy would predict their observed moves most accurately?

            After your reasoning, select one strategy and output its description in the following Python dictionary format, parsable by ast.literal_eval():
            ```python
            {{
                'Opponent_strategy': ''
            }}
            ```
            """
        return user_message

    def generate_interaction_feedback_user_message(
            self, 
            step,
            possible_opponent_strategy=None):
        
        if possible_opponent_strategy is None:
            possible_opponent_strategy = self.possible_opponent_strategy
        user_message = f"""
            An interaction with the other player has occurred at round {step-1}, {self.interaction_history[-1]}.
            The total interaction history is: {self.interaction_history}.
            You last played: {self.interaction_history[-1]['my_play']}
            You previously guessed that their policy or strategy is: {possible_opponent_strategy}.
            High-level strategy Request:
            Provide the next high-level strategy for player {self.agent_id}. 
            Think step by step in parts 1 and 2 about which strategy to select based on the entire interaction history in the following format:
            1. 'predicted_opponent_next_play': Given the above mentioned guess about the opponent's policy/strategy, and the last action you played (if their strategy is adaptive, it may not be), what is their likely play in the next round.
            2. 'my_next_play': Given the opponent's likely play in the next round, what should your next play be to counter this?
            3. In the 3rd part of your response, output the predicted opponent's next play and your next play as either 'rock', 'paper', or 'scissors' (use no other string) in following Python dictionary format, parsable by `ast.literal_eval()` starting with ```python.
            Example response:
            1. 'predicted_opponent_next_play': Given that my opponent is playing a rock policy, I believe their next play will be a rock.
            2. 'my_next_play': Given that my opponent is playing a rock policy, I believe my next play should be paper.
            ```python
            {{
              'predicted_opponent_next_play': 'rock',
              'my_next_play': 'paper'
            }}
            """

        return user_message

    async def parse_and_validate_response(self, response_type, system_message, user_message, initial_response, max_retries=20):
        """
        Parse and validate responses, retrying if necessary.
        response_type: 'strategy' or 'next_plays'
        """
        correct_syntax = False
        counter = 0
        response = initial_response
        
        while not correct_syntax and counter < max_retries:
            try:
                if self.n == 1:
                    parsed_dict = self.extract_dict(response)
                else:
                    response, parsed_dict = self.parse_multiple_llm_responses(response, response_type=response_type)
                
                if response_type == 'strategy':
                    # Validate strategy selection
                    if 'Opponent_strategy' in parsed_dict:
                        correct_syntax = True
                        return response, parsed_dict
                
                elif response_type == 'next_plays':
                    # Validate next plays
                    both_keys_present = ('predicted_opponent_next_play' in parsed_dict) and ('my_next_play' in parsed_dict)
                    correct_format = parsed_dict['my_next_play'] in ['rock', 'paper', 'scissors'] and \
                                parsed_dict['predicted_opponent_next_play'] in ['rock', 'paper', 'scissors']
                    
                    if both_keys_present and correct_format:
                        correct_syntax = True
                        return response, parsed_dict
                
                # If we get here, validation failed
                print(f"Error parsing {response_type} dictionary, retrying...")
                responses = await asyncio.gather(
                    *[self.controller.async_batch_prompt(system_message, [user_message])]
                )
                response = responses[0][0]
                
            except Exception as e:
                print(f"Error parsing response: {e}, retrying...")
                responses = await asyncio.gather(
                    *[self.controller.async_batch_prompt(system_message, [user_message])]
                )
                response = responses[0][0]
            
            counter += 1
        
        # If we've exhausted retries, return default values
        if response_type == 'strategy':
            return response, {'Opponent_strategy': ''}  # Default strategy
        else:
            return response, {'predicted_opponent_next_play': 'rock', 'my_next_play': 'paper'}  # Default moves

    async def tom_module(self, interaction_history, step):
        if len(interaction_history) > 50:
            self.interaction_history = interaction_history[-50:]
        else:
            self.interaction_history = interaction_history
        self.reward_tracker[self.agent_id] += interaction_history[-1]['my_reward']

        # First select which strategy opponent is using
        strategy_msg = self.generate_strategy_selection_message(step)
        responses = await asyncio.gather(
            *[self.controller.async_batch_prompt(self.system_message, [strategy_msg])]
        )
        initial_response = responses[0][0]
        
        # Parse and validate strategy selection
        response, strategy_selection = await self.parse_and_validate_response(
            'strategy', 
            self.system_message, 
            strategy_msg,
            initial_response
        )
        
        # Get the selected strategy description
        self.possible_opponent_strategy = strategy_selection['Opponent_strategy']

        # Now do action selection based on selected strategy
        hls_user_msg2 = self.generate_interaction_feedback_user_message(step)
        responses = await asyncio.gather(
            *[self.controller.async_batch_prompt(self.system_message, [hls_user_msg2])]
        )
        action_response = responses[0][0]
        
        # Parse and validate next plays
        response, next_plays = await self.parse_and_validate_response(
            'next_plays',
            self.system_message,
            hls_user_msg2,
            action_response
        )
        
        self.next_plays = deepcopy(next_plays)
        next_play = self.next_plays['my_next_play']
        
        full_response = f"{initial_response}\n\n{action_response}"
        #final_response = f"{response}\n\nSelected strategy: {self.possible_opponent_strategy}"
        return full_response, strategy_msg + "\n\n" + hls_user_msg2, next_play

    def extract_dict(self, response):
        try:
            # Find the start of the dictionary by looking for the "```python\n" or "\n```" delimiter
            start_marker = "```python\n"
            end_marker = "\n```"
            start_index = response.find(start_marker)
            if start_index != -1:
                start_index += len(start_marker)
            else:
                # If "```python\n" is not found, look for "\n```"
                start_marker = "\n```\n"
                end_marker = "```"
                start_index = response.find(start_marker)
                if start_index != -1:
                    start_index += len(start_marker)
                else:
                    raise ValueError("Python dictionary markers not found in GPT-4's response.")
            
            end_index = response.find(end_marker, start_index)
            if end_index == -1:
                raise ValueError("Python dictionary markers not found in GPT-4's response.")
            
            dict_str = response[start_index: end_index].strip()

            # Process each line, skipping lines that are comments
            lines = dict_str.split('\n')
            cleaned_lines = []
            for line in lines:
                # Check if line contains a comment
                comment_index = line.find('#')
                if comment_index != -1:
                    # Exclude the comment part
                    line = line[:comment_index].strip()
                if line:  # Add line if it's not empty
                    cleaned_lines.append(line)

            # Reassemble the cleaned string
            cleaned_dict_str = ' '.join(cleaned_lines)
            
            # Convert the string representation of a dictionary into an actual dictionary
            extracted_dict = ast.literal_eval(cleaned_dict_str)
            return extracted_dict
        except Exception as e:
            print(f"Error parsing dictionary: {e}")
            return {}

    def parse_multiple_llm_responses(self, responses, response_type=None, state=None):
        """Parses the llms multiple responses when n > 1."""
        if response_type == 'next_plays':
            for i, response in enumerate(responses):
                response_dict = self.extract_dict(response)
                if response_dict == {}:
                    continue
                elif 'predicted_opponent_next_play' not in response_dict:
                    continue
                elif 'my_next_play' not in response_dict:
                    continue
                else:
                    return response, response_dict
        else:
            for i, response in enumerate(responses):
                response_dict = self.extract_dict(response)
                if response_dict == {}:
                    continue
                else:
                    return response, response_dict
                
            return '', {}
