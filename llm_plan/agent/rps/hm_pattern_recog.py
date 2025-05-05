import re
import abc
import ast
import asyncio
from copy import deepcopy
import numpy as np
from queue import Queue
from typing import List, Dict, Any, Tuple, Optional


class PatternHypotheticalMinds(abc.ABC):
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
        self.pattern_hypotheses = {}
        self.interaction_num = 0
        self.reward_tracker = {self.agent_id: 0}
        self.good_hypothesis_found = False
        self.alpha = 0.3  # learning rate for updating hypothesis values
        self.correct_guess_reward = 1
        self.good_hypothesis_thr = 0.7
        self.top_k = config.get('top_k', 5)
        self.n = config['n']
        self.t = config.get('t', 50)  # show last t rounds of interaction history
        self.self_improve = config['self_improve']

    def generate_system_message(self):
        self.system_message = f"""
            You are an intelligent pattern recognition system analyzing sequences.
            You will be analyzing a sequence of patterns represented as A, B, and C.
            Each entry in the sequence history contains:
            - 'index': the sequence position
            - '1': a value (A, B, or C) that you need to predict
            - '2': another value (A, B, or C)
            - '3': another value (X, Y, or Z)
            
            Your task is to identify patterns in the '1' values and predict what the next '1' value will be.
            Focus purely on detecting patterns in the sequence.
            """

    def generate_hypothesis_user_message(
            self,
            metrics,
            step):
        metrics_str = "\n".join(f"- {agent}: {metric}" for agent, metric in metrics.items())
        # get the top N hypotheses
        sorted_keys = sorted([key for key in self.pattern_hypotheses],
                    key=lambda x: self.pattern_hypotheses[x]['value'],
                    reverse=True)
        top_keys = sorted_keys[:self.top_k]
        # show top hypotheses with value > 0
        self.top_hypotheses = {key: self.pattern_hypotheses[key] for key in top_keys if self.pattern_hypotheses[key]['value'] > 0}

        if self.self_improve:
            hypothesis_request = f"""
                A new interaction occurred at round {step-1}, {self.interaction_history[-1]}.
                The sequence history is: {self.interaction_history}.
                Here are your previous hypotheses about the underlying pattern: {self.top_hypotheses}.
                
                What is the likely pattern governing the 'their_choice' values in this sequence? Think step by step about this given the history.
                If your previous hypotheses are useful, you can iterate and refine them to get a better explanation of the data observed so far.
                If a hypothesis already explains the data very well, then repeat the hypothesis in this response.
                
                The pattern may be simple (e.g., repeating sequence) or complex (e.g., dependent on previous elements or positions).
                Look for regularities in the sequence. Is there a consistent pattern after certain elements appear?
                
                Once you have developed a hypothesis about the pattern with step-by-step reasoning, you can use this hypothesis to predict the next 'their_choice' value.
                
                In the 2nd part of your response, summarize your hypothesis in a concise message following Python dictionary format, parsable by `ast.literal_eval()` starting with ```python.
                This summary will be shown to you in the future to help you predict the next element.
                
                Example summary:
                ```python
                {{
                'Pattern_hypothesis': ''
                }}
                ```

                You will be prompted again shortly to predict the next element, so do not include that in your response yet.
                """
        else:
            hypothesis_request = f"""
                A new interaction occurred at round {step-1}, {self.interaction_history[-1]}.
                The sequence history is: {self.interaction_history}.
                
                What is the likely pattern governing the '1' values in this sequence? Think step by step about this given the history.
                Look for regularities in the sequence. Is there a consistent pattern after certain elements appear?
                
                Once you have developed a hypothesis about the pattern with step-by-step reasoning, you can use this hypothesis to predict the next '1' value.
                
                In the 2nd part of your response, summarize your hypothesis in a concise message following Python dictionary format, parsable by `ast.literal_eval()` starting with ```python.
                This summary will be shown to you in the future to help you predict the next element.
                
                Example summary:
                ```python
                {{
                'Pattern_hypothesis': ''
                }}
                ```

                You will be prompted again shortly to predict the next element, so do not include that in your response yet.
                """

        user_message = f"""Metrics: {metrics_str}

            {hypothesis_request}
            """
        return user_message

    def generate_prediction_user_message(
            self,
            step,
            possible_pattern_hypothesis=None):

        if possible_pattern_hypothesis is None:
            possible_pattern_hypothesis = self.possible_pattern_hypothesis
        user_message = f"""
            A new interaction occurred at round {step}, {self.interaction_history[-1]}.
            The sequence history is: {self.interaction_history}.
            Your previously generated hypothesis about the pattern is: {possible_pattern_hypothesis}.
            
            Based on your hypothesis about the pattern and the sequence history, what will be the next '1' value?
            Think step by step about the pattern and explain your reasoning.
            
            In the 2nd part of your response, output your prediction as either 'A', 'B', or 'C' (use no other string) in the following Python dictionary format, parsable by `ast.literal_eval()` starting with ```python.
            
            Example response:
            Based on my hypothesis that the pattern is always B for '1', I believe the next value will be B.
            
            ```python
            {{
              'predicted_next_element': 'B'
            }}
            ```
            """

        return user_message

    async def tom_module(self, interaction_history, step):
        # Save original history for evaluation
        self.original_history = interaction_history
        
        # Transform interaction history to abstract format
        if len(interaction_history) > self.t:
            self.interaction_history = self.transform_interaction_history(interaction_history[-self.t:])
        else:
            self.interaction_history = self.transform_interaction_history(interaction_history)
        
        # Update metrics based on the latest observation
        self.reward_tracker[self.agent_id] += interaction_history[-1]['my_reward']
        
        hypothesis_user_msg = ''
        hypothesis_response = ''
        
        # Evaluate existing hypotheses based on the latest observation
        if self.interaction_num > 1:
            self.eval_hypotheses()
            
        if not self.good_hypothesis_found:
            # Generate new hypotheses if we haven't found a good one yet
            hypothesis_user_msg1 = self.generate_hypothesis_user_message(self.reward_tracker, step)
            hypothesis_user_msg = hypothesis_user_msg + hypothesis_user_msg1
            
            responses = await asyncio.gather(
                *[self.controller.async_batch_prompt(self.system_message, [hypothesis_user_msg1])]
            )
            response = responses[0][0]
            
            if self.n == 1:
                possible_pattern_hypothesis = self.extract_dict(response)
            else:
                response, possible_pattern_hypothesis = self.parse_multiple_llm_responses(response)
                
            self.possible_pattern_hypothesis = deepcopy(possible_pattern_hypothesis)
            self.pattern_hypotheses[self.interaction_num] = deepcopy(possible_pattern_hypothesis)
            
            # Initialize the value of this hypothesis
            self.pattern_hypotheses[self.interaction_num]['value'] = 0
            
            # Add response to hypothesis_response after two new lines
            top_hypotheses_summary = f"""Top hypotheses: {self.top_hypotheses}"""
            hypothesis_response = hypothesis_response + '\n\n' + top_hypotheses_summary + '\n\n' + response

            # Predict next element for latest hypothesis and the top k so far
            prediction_user_msg = self.generate_prediction_user_message(step)
            hypothesis_user_msg = hypothesis_user_msg + '\n\n' + prediction_user_msg
            user_messages = [prediction_user_msg]
            
            # Sort hypotheses by value in descending order
            sorted_keys = sorted([key for key in self.pattern_hypotheses if key != self.interaction_num],
                    key=lambda x: self.pattern_hypotheses[x]['value'],
                    reverse=True)
                    
            # Loop through the top k keys
            for key in sorted_keys[:self.top_k]:
                possible_pattern_hypothesis = self.pattern_hypotheses[key]
                prediction_user_msg = self.generate_prediction_user_message(step, possible_pattern_hypothesis)
                user_messages.append(prediction_user_msg)

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
                        next_prediction = self.extract_dict(response)
                    else:
                        response, next_prediction = self.parse_multiple_llm_responses(response, response_type='next_prediction')
                        
                    # Check for correct formatting
                    has_prediction_key = 'predicted_next_element' in next_prediction
                    correct_format = has_prediction_key and next_prediction['predicted_next_element'] in ['A', 'B', 'C']
                    
                    if not correct_format:
                        correct_syntax = False
                        print(f"Error parsing dictionary when extracting next prediction, retrying...")
                        break
                        
                    if i == 0:
                        self.next_prediction = deepcopy(next_prediction)
                        self.pattern_hypotheses[self.interaction_num]['next_prediction'] = deepcopy(self.next_prediction)
                        next_prediction_response = deepcopy(response)
                    else:
                        self.pattern_hypotheses[sorted_keys[i-1]]['next_prediction'] = deepcopy(next_prediction)
                counter += 1

            if counter >= 20 and not correct_syntax:
                print("All attempts failed. Using default values.")
                default_prediction = {
                    'predicted_next_element': 'A'
                }
                self.next_prediction = deepcopy(default_prediction)
                self.pattern_hypotheses[self.interaction_num]['next_prediction'] = deepcopy(default_prediction)
                next_prediction_response = "Failed to get valid response. Using default values."

            # Add response to hypothesis_response after two new lines
            hypothesis_response = hypothesis_response + '\n\n' + next_prediction_response
        else:
            # Skip asking about pattern when we have a good hypothesis
            # Sort the keys of self.pattern_hypotheses based on 'value', in descending order
            sorted_keys = sorted([key for key in self.pattern_hypotheses], 
                                key=lambda x: self.pattern_hypotheses[x]['value'], 
                                reverse=True)
                                
            # Set the possible pattern hypothesis to the top hypothesis
            best_key = sorted_keys[0]
            
            # Assert the value of the best key is above the threshold
            assert self.pattern_hypotheses[best_key]['value'] > self.good_hypothesis_thr
            
            self.possible_pattern_hypothesis = deepcopy(self.pattern_hypotheses[best_key])
            good_hypothesis_summary = f"""Good hypothesis found: {self.possible_pattern_hypothesis}"""
            
            # Add summary to hypothesis_response after two new lines
            hypothesis_response = hypothesis_response + '\n\n' + good_hypothesis_summary
            
            prediction_user_msg = self.generate_prediction_user_message(step)
            hypothesis_user_msg = hypothesis_user_msg + '\n\n' + prediction_user_msg

            # Make sure output dict syntax is correct
            correct_syntax = False
            counter = 0
            while not correct_syntax and counter < 20:
                correct_syntax = True
                # Gathering responses asynchronously
                responses = await asyncio.gather(
                    *[self.controller.async_batch_prompt(self.system_message, [prediction_user_msg])]
                    )
                response = responses[0][0]
                
                if self.n == 1:
                    next_prediction = self.extract_dict(response)
                else:
                    response, next_prediction = self.parse_multiple_llm_responses(response, response_type='next_prediction')
                    
                # Check for correct formatting
                has_prediction_key = 'predicted_next_element' in next_prediction
                correct_format = has_prediction_key and next_prediction['predicted_next_element'] in ['A', 'B', 'C']
                
                if not correct_format:
                    correct_syntax = False
                    print(f"Error parsing dictionary when extracting next prediction, retrying...")
                counter += 1
                
            self.next_prediction = deepcopy(next_prediction)
            self.pattern_hypotheses[best_key]['next_prediction'] = deepcopy(self.next_prediction)
            
            # Add response to hypothesis_response after two new lines
            hypothesis_response = hypothesis_response + '\n\n' + response

        predicted_next = self.next_prediction['predicted_next_element']
        my_next_move = self.get_action_from_prediction(predicted_next)

        self.interaction_num += 1
        return hypothesis_response, hypothesis_user_msg, my_next_move

    def map_move_to_abc(self, move):
        """Map 'rock', 'paper', 'scissors' to 'A', 'B', 'C'"""
        mapping = {
            'rock': 'A',
            'paper': 'B',
            'scissors': 'C'
        }
        return mapping.get(move, 'A')

    def map_reward_to_xyz(self, reward):
        """Map reward values to 'X', 'Y', 'Z'"""
        mapping = {
            -1: 'X',
            3: 'Y',
            0: 'Z'
        }
        return mapping.get(reward, 'Z')

    def transform_interaction_history(self, original_history):
        """Transform the original interaction history into abstract format"""
        transformed_history = []
        for entry in original_history:
            transformed_entry = {
                'index': entry['round'],
                '1': self.map_move_to_abc(entry['opponent_play']),
                '2': self.map_move_to_abc(entry['my_play']),
                '3': self.map_reward_to_xyz(entry['my_reward'])
            }
            transformed_history.append(transformed_entry)
        return transformed_history

    def get_action_from_prediction(self, prediction):
        """Map predicted element (A, B, C) to winning move (rock, paper, scissors)"""
        winning_moves = {
            'A': 'paper',   # If opponent plays A (Rock), agent plays paper
            'B': 'scissors', # If opponent plays B (Paper), agent plays scissors
            'C': 'rock',    # If opponent plays C (Scissors), agent plays rock
        }
        return winning_moves.get(prediction, 'paper')

    def eval_hypotheses(self):
        latest_key = max(self.pattern_hypotheses.keys())
        
        # Sort the keys by value in descending order
        sorted_keys = sorted([key for key in self.pattern_hypotheses if key != latest_key],
                    key=lambda x: self.pattern_hypotheses[x]['value'],
                    reverse=True)
                    
        keys2eval = sorted_keys[:self.top_k] + [latest_key]
        
        # Loop through the top N keys and the latest key
        self.good_hypothesis_found = False
        for key in keys2eval:
            if 'predicted_next_element' not in self.pattern_hypotheses[key]['next_prediction']:
                print("Error: predicted_next_element not found in hypothesis")
                continue
                
            predicted_next_element = self.pattern_hypotheses[key]['next_prediction']['predicted_next_element']
            actual_next_element = self.interaction_history[-1]['1']
            
            # Check if the prediction was correct
            correct_prediction = predicted_next_element == actual_next_element
            
            # Update value using Rescorla-Wagner
            if correct_prediction:
                prediction_error = self.correct_guess_reward - self.pattern_hypotheses[key]['value']
            else:
                prediction_error = -self.correct_guess_reward - self.pattern_hypotheses[key]['value']
                
            self.pattern_hypotheses[key]['value'] = self.pattern_hypotheses[key]['value'] + (self.alpha * prediction_error)

            if self.pattern_hypotheses[key]['value'] > self.good_hypothesis_thr:
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
                    raise ValueError("Python dictionary markers not found in response.")

            end_index = response.find(end_marker, start_index)
            if end_index == -1:
                raise ValueError("Python dictionary markers not found in response.")

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
        """Parses the LLM's multiple responses when n > 1."""
        if response_type == 'next_prediction':
            for i, response in enumerate(responses):
                response_dict = self.extract_dict(response)
                if response_dict == {}:
                    continue
                elif 'predicted_next_element' not in response_dict:
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