import os
import asyncio
import argparse
import importlib
import json
import numpy as np

from environments.rps_sequential_opponent import run_episode
from llm_plan.agent.rps.sequential_opponent_globals import ACTION_MATRIX_LOOKUP, SEQUENTIAL_OPPONENTS
from llm_plan.agent.rps.sequential_opponent import SelfTransition, OppTransition, OutcomeTransition, PrevTransitionOutcomeTransition
from llm_plan.agent.agent_config import agent_config
from llm_plan.controller.async_llm import AsyncChatLLM
from llm_plan.controller.async_gpt_controller import AsyncGPTController


# TODO: put this somewhere sensible
SOFTMAX_LOOKUP = {
    'default': {'gpt4': 0.2, 'gpt4o': 0.2, 'gpt-4o-mini': 0.2, 'gpt35': 0.2, 'llama3': 0.7},
    'high': {'gpt4': 0.8, 'gpt4o': 0.8, 'gpt-4o-mini': 0.8, 'gpt35': 0.8, 'llama3': 1.0} # TODO set values here
}


def setup_sequential_agent(sequential_agent, sequential_agent_actions):
    if sequential_agent in ['self_transition_up', 'self_transition_down']:  # self transition agents
        return SelfTransition(id=sequential_agent, action_matrix=sequential_agent_actions)
    elif sequential_agent in ['opponent_transition_up', 'opponent_transition_stay']:  # opponent transition agents
        return OppTransition(id=sequential_agent, action_matrix=sequential_agent_actions)
    elif sequential_agent in ['W_stay_L_up_T_down', 'W_up_L_down_T_stay']:  # outcome transition agents
        return OutcomeTransition(id=sequential_agent, action_matrix=sequential_agent_actions)
    elif sequential_agent == 'prev_outcome_prev_transition':  # previous outcome, previous transition agent
        return PrevTransitionOutcomeTransition(id=sequential_agent, action_matrix=sequential_agent_actions)
    else:
        raise ValueError(f"Unknown opponent type: {sequential_agent}")

def setup_tom_agent(api_key, model_id, model_settings, agent_type, llm_type, sequential_opponent):
    # configure llm
    if llm_type == 'gpt4':
        llm = AsyncChatLLM(kwargs={'api_key': api_key, 'model': 'gpt-4-1106-preview'})
    elif llm_type == 'gpt4o':
        llm = AsyncChatLLM(kwargs={'api_key': api_key, 'model': 'gpt-4o-2024-08-06'})
    elif llm_type == 'gpt-4o-mini':
        llm = AsyncChatLLM(kwargs={'api_key': api_key, 'model': 'gpt-4o-mini'})
    elif llm_type == 'gpt35':
        llm = AsyncChatLLM(kwargs={'api_key': api_key, 'model': 'gpt-3.5-turbo-1106'})
    elif llm_type == 'llama3':
        kwargs = {
            'api_key': "EMPTY",
            'base_url': "http://localhost",
            'port': 8000,
            'version': 'v1',
            'model': 'meta-llama/Meta-Llama-3-70B-Instruct'
        }
        llm = AsyncChatLLM(kwargs=kwargs)
    elif llm_type == 'mixtral':
        kwargs = {
            'api_key': "EMPTY",
            'base_url': "http://localhost",
            'port': 8000,
            'version': 'v1',
            'model': 'mistralai/Mixtral-8x7B-Instruct-v0.1'
        }
        llm = AsyncChatLLM(kwargs=kwargs)
    else:
        raise ValueError(f"Unknown LLM type: {llm_type}")

    # configure agent
    agent_config_obj = {'agent_id': model_id}
    agent_config_obj['n'] = model_settings['n']
    agent_config_obj['temperature'] = model_settings['temperature'] # eb
    agent_config_obj['top_k'] = model_settings['top_k'] # eb

    if 'hypothetical_minds' in agent_type or 'hm' in agent_type:
        agent_config_obj['self_improve'] = True

    agent_class_path = agent_config[agent_type]
    agent_module_path, agent_class_name = agent_class_path.rsplit('.', 1)
    agent_module = importlib.import_module(agent_module_path)
    agent_class = getattr(agent_module, agent_class_name)

    if 'hypothetical_minds' in agent_type or 'hm' in agent_type:
        agent_config_obj['self_improve'] = True

    if 'give_hypothesis' in agent_type:
        agent_config_obj['sequential_opponent'] = sequential_opponent

    # configure controller
    del model_settings['top_k'] # eb: remove so we don't mess up downstream controller behavior
    controller = AsyncGPTController(
        llm=llm,
        model_id=model_id,
        **model_settings
    )

    agent = agent_class(agent_config_obj, controller)

    agent.agent_type = agent_type  # add any changes from default
    agent.sequential_opponent = sequential_opponent
    agent.llm_type = llm_type
    return agent

async def main_async(agent_type, llm_type, sequential_opponent, softmax, num_hypotheses, num_rounds=300, seed=None):
    # Set random seed for reproducibility if needed
    if seed is not None:
        np.random.seed(seed)

    # Initialize sequential agent
    sequential_agent = setup_sequential_agent(sequential_opponent, ACTION_MATRIX_LOOKUP[sequential_opponent])

    # Load API key
    api_key_path = './llm_plan/lc_api_key.json'
    OPENAI_KEYS = json.load(open(api_key_path, 'r'))
    api_key = OPENAI_KEYS['API_KEY']
    model_id = 'player_0'

    # Set model settings based on llm_type
    if llm_type == 'gpt4':
        model_settings = {
            "model": "gpt-4-1106-preview",
            "max_tokens": 4000,
            "temperature": softmax,
            "top_p": 1.0,
            "n": 1,
            "top_k": num_hypotheses, # eb: num hypotheses
        }
    elif llm_type == 'gpt4o':
        model_settings = {
            "model": "gpt-4o-2024-08-06",
            "max_tokens": 4000,
            "temperature": softmax,
            "top_p": 1.0,
            "n": 1,
            "top_k": num_hypotheses, # eb: num hypotheses
        }
    elif llm_type == 'gpt-4o-mini':
        model_settings = {
            "model": "gpt-4o-mini",
            "max_tokens": 4000,
            "temperature": softmax,
            "top_p": 1.0,
            "n": 1,
            "top_k": num_hypotheses, # eb: num hypotheses
        }
    elif llm_type == 'gpt35':
        model_settings = {
            "model": "gpt-3.5-turbo-1106",
            "max_tokens": 2000,
            "temperature": softmax,
            "top_p": 1.0,
            "n": 1,
            "top_k": num_hypotheses, # eb: num hypotheses
        }
    elif llm_type == 'llama3':
        model_settings = {
            "model": "meta-llama/Meta-Llama-3-70B-Instruct",
            "max_tokens": 2000,
            "temperature": softmax,
            "top_p": 1.0,
            "n": 10,
            "top_k": num_hypotheses, # eb: num hypotheses
        }
    else:
        raise ValueError(f"Unknown llm_type: {llm_type}")

    # Set up TOM agent
    tom_agent = setup_tom_agent(api_key, model_id, model_settings, agent_type, llm_type, sequential_opponent)

    # Run the game
    await run_episode(tom_agent, sequential_agent, num_rounds=num_rounds, seed=seed)

def main():
    parser = argparse.ArgumentParser(description='Run a game of rock paper scissors')
    parser.add_argument('--agent_type', type=str, default='hm', help='Agent type')
    parser.add_argument('--llm_type', type=str, default='gpt4o', help='LLM Type')
    parser.add_argument('--sequential_opponent', type=str, default='self_transition_up', help=f'Sequential opponent type: {SEQUENTIAL_OPPONENTS}')
    parser.add_argument('--softmax', type=float, default=0.2, help='Softmax temperature (default: 1)')
    parser.add_argument('--num_hypotheses', type=int, default=5, help='Number of hypotheses to consider (default: 5)')
    parser.add_argument('--num_rounds', type=int, default=300, help='Number of rounds to play')
    args = parser.parse_args()

    # Run the game
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main_async(args.agent_type, args.llm_type, args.sequential_opponent, args.softmax, args.num_hypotheses, args.num_rounds))

if __name__ == "__main__":
    main()