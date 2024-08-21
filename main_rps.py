import os
import asyncio
import argparse
import json

from environments.rps_sequential_opponent import run_episode, run_sequential_episode # TESTING
from llm_plan.agent.rps.sequential_opponent_globals import ACTION_MATRIX_LOOKUP, SEQUENTIAL_OPPONENTS
from llm_plan.agent.rps.sequential_opponent import SelfTransition, OppTransition, OutcomeTransition
from llm_plan.agent.rps.rps_hypothetical_minds import DecentralizedAgent
# TESTING: comment out everything below
from llm_plan.agent.agent_config import agent_config
from llm_plan.controller.async_llm import AsyncChatLLM
from llm_plan.controller.async_gpt_controller import AsyncGPTController



def setup_sequential_agent(sequential_agent, sequential_agent_actions):
    if sequential_agent in ['self_transition_up', 'self_transition_down']: # self transition agents
        return SelfTransition(id=sequential_agent, action_matrix=sequential_agent_actions)
    elif sequential_agent in ['opponent_transition_up', 'opponent_transition_stay']: # opponent transition agents
        return OppTransition(id=sequential_agent, action_matrix=sequential_agent_actions)
    elif sequential_agent in ['W_stay_L_up_T_down', 'W_up_L_down_T_stay']: # outcome transition agents
        return OutcomeTransition(id=sequential_agent, action_matrix=sequential_agent_actions)
    # TODO final agent: outcome previous transition
    else:
        raise ValueError(f"Unknown opponent type: {sequential_agent}")


def setup_tom_agent(api_key, model_id, model_settings, agent_type, llm_type='gpt4'):
    if llm_type == 'gpt4':
        llm = AsyncChatLLM(kwargs={'api_key': api_key, 'model': 'gpt-4-1106-preview'})
        controller = AsyncGPTController(
            llm=llm,
            model_id=model_id,
            **model_settings
        )
    elif llm_type == 'gpt4o':
        llm = AsyncChatLLM(kwargs={'api_key': api_key, 'model': 'gpt-4o-2024-08-06'})
        controller = AsyncGPTController(
            llm=llm,
            model_id=model_id,
            **model_settings
        )
    elif llm_type == 'gpt-4o-mini':
        llm = AsyncChatLLM(kwargs={'api_key': api_key, 'model': 'gpt-4o-mini'})
        controller = AsyncGPTController(
            llm=llm,
            model_id=model_id,
            **model_settings
        )
    elif llm_type == 'gpt35':
        llm = AsyncChatLLM(kwargs={'api_key': api_key, 'model': 'gpt-3.5-turbo-1106'})
        controller = AsyncGPTController(
            llm=llm,
            model_id=model_id,
            **model_settings
        )
    elif llm_type == 'llama3':
        kwargs = {
            'api_key': "EMPTY",
            'base_url': "http://localhost",
            'port': 8000,
            'version': 'v1',
            'model': 'meta-llama/Meta-Llama-3-70B-Instruct'
        }
        llm = AsyncChatLLM(kwargs=kwargs)
        controller = AsyncGPTController(
            llm=llm,
            model_id=model_id,
            **model_settings
        )
    elif llm_type == 'mixtral':
        kwargs = {
            'api_key': "EMPTY",
            'base_url': "http://localhost",
            'port': 8000,
            'version': 'v1',
            'model': 'mistralai/Mixtral-8x7B-Instruct-v0.1'
        }
        llm = AsyncChatLLM(kwargs=kwargs)
        controller = AsyncGPTController(
            llm=llm,
            model_id=model_id,
            **model_settings
        )

    agent_config_obj = {'agent_id': model_id}

    if 'hypothetical_minds' in agent_type or 'hm' in agent_type:
        agent_config_obj['self_improve'] = True

    agent = DecentralizedAgent(agent_config_obj, controller)
    agent.llm_type = llm_type
    return agent




def main():
    parser = argparse.ArgumentParser(description='Run a game of rock paper scissors')
    parser.add_argument('--llm_type', type=str, default='gpt4o', help='LLM Type')
    parser.add_argument('--sequential_opponent', type=str, default='self_transition_up', help=f'Sequential opponent type: {SEQUENTIAL_OPPONENTS}')
    args = parser.parse_args()

    # Initialize sequential agent
    sequential_agent = setup_sequential_agent(args.sequential_opponent, ACTION_MATRIX_LOOKUP[args.sequential_opponent])

    # Initialize tom agent
    # TESTING: uncomment two lines below
    # tom_agent = setup_sequential_agent(args.sequential_opponent, ACTION_MATRIX_LOOKUP[args.sequential_opponent])
    # run_sequential_episode(tom_agent, sequential_agent, num_rounds=10)
    # TESTING: comment out everything below

    api_key = os.getenv('OPENAI_API_KEY')
    api_key_path = './llm_plan/lc_api_key.json'
    OPENAI_KEYS = json.load(open(api_key_path, 'r'))
    api_key = OPENAI_KEYS['API_KEY']
    model_id = 'player_0'
    if args.llm_type == 'gpt4':
        model_settings = {
            "model": "gpt-4-1106-preview",
            "max_tokens": 4000,
            "temperature": 0.2,
            "top_p": 1.0,
            "n": 1,
        }
    elif args.llm_type == 'gpt4o':
        model_settings = {
            "model": "gpt-4o-2024-08-06",
            "max_tokens": 4000,
            "temperature": 0.2,
            "top_p": 1.0,
            "n": 1,
        }
    elif args.llm_type == 'gpt-4o-mini':
        model_settings = {
            "model": "gpt-4o-mini",
            "max_tokens": 4000,
            "temperature": 0.2,
            "top_p": 1.0,
            "n": 1,
        }
    elif args.llm_type == 'gpt35':
        model_settings = {
            "model": "gpt-3.5-turbo-1106",
            "max_tokens": 2000,
            "temperature": 0.2,
            "top_p": 1.0,
            "n": 1,
        }
    tom_agent = setup_tom_agent(api_key, model_id, model_settings, agent_type='hm', llm_type=args.llm_type)

    # Run game
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_episode(tom_agent, sequential_agent, num_rounds=300))

if __name__ == "__main__":
    main()