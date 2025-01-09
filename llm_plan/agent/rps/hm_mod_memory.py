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
        self.memory_states = {}
        self.interact_steps = 0
        self.interaction_history = []
        self.opponent_hypotheses = {}
        self.interaction_num = 0
        self.reward_tracker = {self.agent_id: 0}
        self.good_hypothesis_found = False
        self.alpha = 0.3 # learning rate for updating hypothesis values
        self.correct_guess_reward = 1
        self.good_hypothesis_thr = 0.7
        self.top_k = 5 # number of top hypotheses to evaluate
        self.n = config['n']
        self.self_improve = config['self_improve']
        player_key = self.agent_id
        opponent_key = ['player_1' if self.agent_id == 'player_0' else 'player_0'][0]
        for entity_type in ['yellow_box', 'blue_box', 'purple_box', 'ground', player_key, opponent_key]:
            self.memory_states[entity_type] = []

    def generate_system_message(self):
        self.system_message = f"""
            You are Agent {self.agent_id} in the two player iterated game of rock paper scissors
            Rock beats scissors, paper beats rock, and scissors beats paper.
            Winner gets 3 reward, loser gets -1 reward, and tie gives 0 reward.
            You will be playing the same opponent for 300 rounds.
            """

    def convert_history(self, old_history):
        """
        Convert a list of old-format RPS interaction records into the new format
        that includes 'my_prev_play' and 'opponent_prev_play'.

        :param old_history: A list of dictionaries, each with the keys:
                            ['round', 'my_play', 'opponent_play', 'my_reward'].
        :return: A new list of dictionaries, each with the keys:
                 ['round', 'my_prev_play', 'opponent_prev_play', 'my_play', 'opponent_play', 'my_reward'].
        """
        new_history = []
        
        for i, record in enumerate(old_history):
            if i == 0:
                # No previous round for round 0
                my_prev_play = None
                opponent_prev_play = None
            else:
                # Use the data from the previous record
                my_prev_play = old_history[i - 1]['my_play']
                opponent_prev_play = old_history[i - 1]['opponent_play']

            new_record = {
                'round': record['round'],
                'my_prev_play': my_prev_play,
                'opponent_prev_play': opponent_prev_play,
                'my_play': record['my_play'],
                'opponent_play': record['opponent_play'],
                'my_reward': record['my_reward']
            }
            new_history.append(new_record)

        return new_history

    def generate_interaction_feedback_user_message1(
            self, 
            total_rewards,
            step):
        rewards_str = "\n".join(f"- {player}: {reward}" for player, reward in total_rewards.items())
        # get the top N hypotheses
        sorted_keys = sorted([key for key in self.opponent_hypotheses],
                    key=lambda x: self.opponent_hypotheses[x]['value'], 
                    reverse=True)
        top_keys = sorted_keys[:self.top_k]
        # show top hypotheses with value > 0
        self.top_hypotheses = {key: self.opponent_hypotheses[key] for key in top_keys if self.opponent_hypotheses[key]['value'] > 0}
        
        if self.self_improve:
            strategy_request = f"""
                An interaction with the other player has occurred at round {step-1}, {self.interaction_history[-1]}.
                The total interaction history is: {self.interaction_history}.
                Here are your previous hypotheses about the algorithm your opponent is playing: {self.top_hypotheses}.
                What is your opponent's likely policy given their plays? Think step by step about this given the interaction history. 
                If your previous hypotheses are useful, you can iterate and refine them to get a better explanation of the data observed so far.
                If a hypothesis already explains the data very well, then repeat the hypothesis in this response.
                They may be playing the same static policy every time, a complex strategy to counter you, or anything in between. 
                They are not necessarily a smart agent that adapts to your strategy, you are just playing an algorithm. 
                Are you getting positive or negative reward when playing the same choice? 
                For example getting positive reward every time you play rock. 
                If so, your opponent may be playing a static strategy and you can exploit this by playing the counter strategy.
                Once you have output a hypothesis about your opponent's strategy with step by step reasoning, you can use hypothesis to inform your strategy. 
                In the 2nd part of your response, summarize your hypothesis in a concise message following Python dictionary format, parsable by `ast.literal_eval()` starting with ```python.
                This summary will be shown to you in the future in order for you to select the appropriate counter strategy.
                Example summary:
                ```python
                {{
                'Opponent_strategy': ''
                }}
                ```
                
                You will be prompted again shortly to select your next play, so do not include that in your response yet right now.
                """
        else:
            strategy_request = f"""
                An interaction with the other player has occurred at round {step-1}, {self.interaction_history[-1]}.
                The total interaction history is: {self.interaction_history}.
                What is your opponent's likely policy given their plays? Think step by step about this given the interaction history. 
                They may be playing the same static policy every time, a complex strategy to counter you, or anything in between. 
                They are not necessarily a smart agent that adapts to your strategy, you are just playing an algorithm. 
                Are you getting positive or negative reward when playing the same choice? 
                For example getting positive reward every time you play rock. 
                If so, your opponent may be playing a static strategy and you can exploit this by playing the counter strategy.
                Once you have output a hypothesis about your opponent's strategy with step by step reasoning, you can use hypothesis to inform your strategy. 
                In the 2nd part of your response, summarize your hypothesis in a concise message following Python dictionary format, parsable by `ast.literal_eval()` starting with ```python.
                This summary will be shown to you in the future in order for you to select the appropriate counter strategy.
                Example summary:
                ```python
                {{
                'Opponent_strategy': ''
                }}
                ```
                
                You will be prompted again shortly to select your next play, so do not include that in your response yet right now.
                """

        user_message = f"""Total Rewards:{rewards_str}

            {strategy_request}
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
        if len(interaction_history) > 50:
            self.interaction_history = interaction_history[-50:]
        else:
            self.interaction_history = interaction_history
        # convert interaction history to new format
        self.interaction_history = self.convert_history(self.interaction_history)
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
                # breakpoint()
                # fill in default value
                self.opponent_hypotheses[key]['next_plays']['predicted_opponent_next_play'] = 'rock'
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
