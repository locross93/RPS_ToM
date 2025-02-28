import re
import abc
import ast
import asyncio
from copy import deepcopy
import numpy as np
from queue import Queue
from typing import List, Dict, Any, Tuple, Optional

from llm_plan.agent import action_funcs


class DecentralizedAgent(abc.ABC):
    def __init__(
            self, 
            config: Dict[str, Any],
            controller: Any,
            ) -> None:
        self.agent_id = config['agent_id']
        self.config = config
        self.controller = controller        
        self.all_actions = Queue()
        self.generate_system_message()
        self.interaction_num = 0
        self.interaction_history = []
        self.reward_tracker = {self.agent_id: 0}
        self.n = config['n']
        self.self_improve = config['self_improve']

    def generate_system_message(self):
        self.system_message = f"""
            You are Agent {self.agent_id} in the two player iterated game of rock paper scissors
            Rock beats scissors, paper beats rock, and scissors beats paper.
            Winner gets 3 reward, loser gets -1 reward, and tie gives 0 reward.
            You will be playing the same opponent for 300 rounds.
            """

    def generate_interaction_feedback_user_message(
            self, 
            step):
        
        user_message = f"""
            An interaction with the other player has occurred at round {step}, {self.interaction_history[-1]}.
            The total interaction history is: {self.interaction_history}.
            You last played: {self.interaction_history[-1]['my_play']}
            Think about what strategy your opponent is playing and select a strategy to counter it based on the interaction history. 
            Then, think step by step in parts 1 and 2 about which action to select in the following format:
            1. 'predicted_opponent_next_play': Given your guess about the opponent's policy/strategy, and the last action you played (if their strategy is adaptive, it may not be), what is their likely play in the next round.
            2. 'my_next_play': Given the opponent's likely play in the next round, what should your next play be to counter this?
            3. In the 3rd part of your response, output the predicted opponent's next play and your next play as either 'rock', 'paper', or 'scissors' (use no other string) in following Python dictionary format, parsable by `ast.literal_eval()` starting with ```python.
            Example response:
            I think my opponent is playing a rock policy, so I believe their next play will be a rock.
            1. 'predicted_opponent_next_play': Given that my opponent is playing a rock policy, I believe their next play will be a rock.
            2. 'my_next_play': Given that my opponent is playing a rock policy, I believe my next play should be paper.
            ```python
            {{
              'predicted_opponent_next_play': 'rock',
              'my_next_play': 'paper'
            }}
            """

        return user_message

    async def tom_module(self, interaction_history, step):
        # if interaction history longer than 50 rounds, just show last 50 rounds
        if len(interaction_history) > 50:
            self.interaction_history = interaction_history[-50:]
        else:
            self.interaction_history = interaction_history
        self.reward_tracker[self.agent_id] += interaction_history[-1]['my_reward']
        hls_user_msg = ''
        hls_response = ''
        hls_user_msg2 = self.generate_interaction_feedback_user_message(step)
        hls_user_msg = hls_user_msg + '\n\n' + hls_user_msg2

        # Make sure output dict syntax is correct
        correct_syntax = False
        counter = 0
        while not correct_syntax and counter < 20:
            correct_syntax = True
            # Gathering responses asynchronously
            responses = await asyncio.gather(
                *[self.controller.async_batch_prompt(self.system_message, [hls_user_msg2])]
                )
            response = responses[0][0]
            if self.n == 1:
                next_plays = self.extract_dict(response)
            else:
                response, next_plays = self.parse_multiple_llm_responses(response, response_type='next_plays')
            both_keys_present = ('predicted_opponent_next_play' in next_plays) and ('my_next_play' in next_plays)
            # check for correct formatting, 'my_next_play' should be either 'rock', 'paper', or 'scissors'
            correct_format = next_plays['my_next_play'] in ['rock', 'paper', 'scissors'] and next_plays['predicted_opponent_next_play'] in ['rock', 'paper', 'scissors']
            if not both_keys_present or not correct_format:
                correct_syntax = False
                print(f"Error parsing dictionary when extracting next plays, retrying...")
            counter += 1
        # add response to hls after two new lines
        hls_response = hls_response + '\n\n' + response
        next_play = next_plays['my_next_play']

        return hls_response, hls_user_msg, next_play

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
