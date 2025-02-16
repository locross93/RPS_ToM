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
        self.interact_steps = 0
        self.interaction_history = []
        self.opponent_hypotheses = {}
        self.interaction_num = 0
        self.reward_tracker = {self.agent_id: 0}
        self.good_hypothesis_found = False
        self.alpha = 0.3 # learning rate for updating hypothesis values
        self.correct_guess_reward = 1
        self.good_hypothesis_thr = 0.7
        self.top_k = config.get('top_k', 5)
        self.n = config['n']
        self.t = config.get('t', 50) # show last t rounds of interaction history

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
            'self_transition_up': f'The opponent {up_transition}',
            'self_transition_down': f'The opponent {down_transition}',
            'opponent_transition_up': f'The opponent {opponent_up_transition}',
            'opponent_transition_stay': f'The opponent {opponent_stay_transition}',
            'W_stay_L_up_T_down': f'After a {win_outcome} the opponent {stay_transition}. After a {loss_outcome} the opponent {up_transition}. After a {tie_outcome} the opponent {down_transition}',
            'W_up_L_down_T_stay': f'After a {win_outcome} the opponent {up_transition}. After a {loss_outcome} the opponent {down_transition}. After a {tie_outcome} the opponent {stay_transition}',
            'prev_outcome_prev_transition': {f'The opponents transition from one round to the next depends on both the previous outcome (win, lose, or tie) and the previous transition the opponent made. \
            After a {win_outcome} in which the opponent {prev_up_transition}, the opponent {up_transition}.\
            After a {win_outcome} in which the opponent {prev_down_transition}, the opponent {down_transition}. \
            After a {win_outcome} in which the opponent {prev_stay_transition}, the opponent {stay_transition}. \
            After a {loss_outcome} in which the opponent {prev_up_transition}, the opponent {stay_transition}.\
            After a {loss_outcome} in which the opponent {prev_down_transition}, the opponent {up_transition}. \
            After a {loss_outcome} in which the opponent {prev_stay_transition}, the opponent {down_transition}. \
            After a {tie_outcome} in which the opponent {prev_up_transition}, the opponent {down_transition}.\
            After a {tie_outcome} in which the opponent {prev_down_transition}, the opponent {stay_transition}. \
            After a {tie_outcome} in which the opponent {prev_stay_transition}, the opponent {up_transition}.'}
        }

    def generate_system_message(self):
        self.system_message = f"""
            You are Agent {self.agent_id} in the two player iterated game of rock paper scissors
            Rock beats scissors, paper beats rock, and scissors beats paper.
            Winner gets 3 reward, loser gets -1 reward, and tie gives 0 reward.
            You will be playing the same opponent for 300 rounds.
            """

    def generate_interaction_feedback_user_message1(
            self,
            total_rewards,
            step):
        # get the top N hypotheses
        sorted_keys = sorted([key for key in self.opponent_hypotheses],
                    key=lambda x: self.opponent_hypotheses[x]['value'],
                    reverse=True)
        top_keys = sorted_keys[:self.top_k]
        # show top hypotheses with value > 0
        self.top_hypotheses = {key: self.opponent_hypotheses[key] for key in top_keys if self.opponent_hypotheses[key]['value'] > 0}
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

    def generate_interaction_feedback_user_message2(
            self,
            step,
            possible_opponent_strategy=None):

        if possible_opponent_strategy is None:
            possible_opponent_strategy = self.possible_opponent_strategy
        user_message = f"""
            An interaction with the other player has occurred at round {step}, {self.interaction_history[-1]}.
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

    async def tom_module(self, interaction_history, step):
        # if interaction history longer than 50 rounds, just show last 50 rounds
        if len(interaction_history) > self.t:
            self.interaction_history = interaction_history[-self.t:]
        else:
            self.interaction_history = interaction_history
        self.reward_tracker[self.agent_id] += interaction_history[-1]['my_reward']
        hls_user_msg = ''
        hls_response = ''
        # score top hypotheses based on last interaction's play
        if self.interaction_num > 1:
            self.eval_hypotheses()
        if not self.good_hypothesis_found:
            hls_user_msg1 = self.generate_interaction_feedback_user_message1(self.reward_tracker, step)
            hls_user_msg = hls_user_msg + hls_user_msg1
            responses = await asyncio.gather(
                *[self.controller.async_batch_prompt(self.system_message, [hls_user_msg1])]
            )
            response = responses[0][0]
            if self.n == 1:
                possible_opponent_strategy = self.extract_dict(response)
            else:
                response, possible_opponent_strategy = self.parse_multiple_llm_responses(response)
            self.possible_opponent_strategy = deepcopy(possible_opponent_strategy)
            self.opponent_hypotheses[self.interaction_num] = deepcopy(possible_opponent_strategy)
            # initialize the value of this hypothesis
            self.opponent_hypotheses[self.interaction_num]['value'] = 0
            # add response to hls after two new lines
            top_hypotheses_summary = f"""Top hypotheses: {self.top_hypotheses}"""
            hls_response = hls_response + '\n\n' + top_hypotheses_summary+ '\n\n' + response

            # predict next opponent play for latest hypothesis and the top k so far
            hls_user_msg2 = self.generate_interaction_feedback_user_message2(step)
            hls_user_msg = hls_user_msg + '\n\n' + hls_user_msg2
            user_messages = [hls_user_msg2]
            # Sort the keys of self.opponent_hypotheses based on 'value', in descending order
            sorted_keys = sorted([key for key in self.opponent_hypotheses if key != self.interaction_num],
                    key=lambda x: self.opponent_hypotheses[x]['value'],
                    reverse=True)
            # Loop through the top k keys
            for key in sorted_keys[:self.top_k]:
                # Access and use the key and its corresponding 'value'
                possible_opponent_strategy = self.opponent_hypotheses[key]
                hls_user_msg2 = self.generate_interaction_feedback_user_message2(step, possible_opponent_strategy)
                user_messages.append(hls_user_msg2)

            # Make sure output dict syntax is correct
            correct_syntax = False
            counter = 0
            while not correct_syntax and counter < 20:
                correct_syntax = True
                # Gathering responses asynchronously
                responses = await asyncio.gather(
                    *[self.controller.async_batch_prompt(self.system_message, [user_msg])
                    for user_msg in user_messages]
                    )
                for i in range(len(responses)):
                    response = responses[i][0]
                    if self.n == 1:
                        next_plays = self.extract_dict(response)
                    else:
                        response, next_plays = self.parse_multiple_llm_responses(response, response_type='next_plays')
                    both_keys_present = ('predicted_opponent_next_play' in next_plays) and ('my_next_play' in next_plays)
                    # check for correct formatting, next plays should contain the keys 'my_next_play' and 'predicted_opponent_next_play'
                    correct_format = 'my_next_play' in next_plays and 'predicted_opponent_next_play' in next_plays
                    # check for correct formatting, 'my_next_play' should be either 'rock', 'paper', or 'scissors'
                    if correct_format:
                        correct_format = next_plays['my_next_play'] in ['rock', 'paper', 'scissors'] and next_plays['predicted_opponent_next_play'] in ['rock', 'paper', 'scissors']
                    if not both_keys_present or not correct_format:
                        correct_syntax = False
                        print(f"Error parsing dictionary when extracting next plays, retrying...")
                        break
                    if i == 0:
                        self.next_plays = deepcopy(next_plays)
                        self.opponent_hypotheses[self.interaction_num]['next_plays'] = deepcopy(self.next_plays)
                        next_play_response = deepcopy(response)
                    else:
                        self.opponent_hypotheses[sorted_keys[i-1]]['next_plays'] = deepcopy(next_plays)
                counter += 1

            if counter >= 20 and not correct_syntax:
                print("All attempts failed. Using default values.")
                default_plays = {
                    'predicted_opponent_next_play': 'rock',
                    'my_next_play': 'paper'
                }
                self.next_plays = deepcopy(default_plays)
                self.opponent_hypotheses[self.interaction_num]['next_plays'] = deepcopy(default_plays)
                next_play_response = "Failed to get valid response. Using default values."

            # add response to hls after two new lines
            hls_response = hls_response + '\n\n' + next_play_response
        else:
            # skip asking about opponent's strategy when we have a good hypothesis
            # Sort the keys of self.opponent_hypotheses based on 'value', in descending order
            sorted_keys = sorted([key for key in self.opponent_hypotheses], key=lambda x: self.opponent_hypotheses[x]['value'], reverse=True)
            # set the possible opponent strategy to the top hypothesis
            best_key = sorted_keys[0]
            # assert the value of the best key is above the threshold
            assert self.opponent_hypotheses[best_key]['value'] > self.good_hypothesis_thr
            self.possible_opponent_strategy = deepcopy(self.opponent_hypotheses[best_key])
            good_hypothesis_summary = f"""Good hypothesis found: {self.possible_opponent_strategy}"""
            # add summary to hls after two new lines
            hls_response = hls_response + '\n\n' + good_hypothesis_summary
            hls_user_msg2 = self.generate_interaction_feedback_user_message2(step)
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
            self.next_plays = deepcopy(next_plays)
            self.opponent_hypotheses[best_key]['next_plays'] = deepcopy(self.next_plays)
            # add response to hls after two new lines
            hls_response = hls_response + '\n\n' + response

        next_play = self.next_plays['my_next_play']

        return hls_response, hls_user_msg, next_play

    def eval_hypotheses(self):
        latest_key = max(self.opponent_hypotheses.keys()) # should this be evaluated when hypothesis is good?
        # Sort the keys of self.opponent_hypotheses based on 'value', in descending order
        sorted_keys = sorted([key for key in self.opponent_hypotheses if key != latest_key],
                    key=lambda x: self.opponent_hypotheses[x]['value'],
                    reverse=True)
        keys2eval = sorted_keys[:self.top_k] + [latest_key]
        # Loop through the top N keys and the latest key
        self.good_hypothesis_found = False
        for key in keys2eval:
            # Access and use the key and its corresponding 'value'
            if 'predicted_opponent_next_play' not in self.opponent_hypotheses[key]['next_plays']:
                breakpoint()
            predicted_opponent_next_play = self.opponent_hypotheses[key]['next_plays']['predicted_opponent_next_play']
            empirical_opp_play = self.interaction_history[-1]['opponent_play']
            # Check if the predicted opponent's next play matches the empirical opponent's last play
            same_play = predicted_opponent_next_play == empirical_opp_play
            if same_play:
                # update the value of this hypothesis with a Rescorla Wagner update
                prediction_error = self.correct_guess_reward - self.opponent_hypotheses[key]['value']
            else:
                prediction_error = -self.correct_guess_reward - self.opponent_hypotheses[key]['value']
            self.opponent_hypotheses[key]['value'] = self.opponent_hypotheses[key]['value'] + (self.alpha * prediction_error)

            if self.opponent_hypotheses[key]['value'] > self.good_hypothesis_thr:
                self.good_hypothesis_found = True

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
