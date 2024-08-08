import os
import asyncio
import numpy as np

from environments.rps_sequential_opponent import run_episode
from llm_plan.agent.rps.sequential_opponent_globals import ACTION_MATRIX_LOOKUP, SEQUENTIAL_OPPONENTS
from llm_plan.agent.rps.sequential_opponent import SelfTransition
from llm_plan.agent.rps.rps_hypothetical_minds import DecentralizedAgent
from llm_plan.agent.agent_config import agent_config
from llm_plan.controller.async_llm import AsyncChatLLM
from llm_plan.controller.async_gpt_controller import AsyncGPTController



def setup_sequential_agent(sequential_opponents, sequential_opponent_actions):
    # Configure a randomly selected sequential agent
    # TODO replace this with argparse / iterating over all opponents
    sequential_agent = np.random.choice(sequential_opponents)

    if sequential_agent == 'self_transition_up':
        return SelfTransition(id=sequential_agent, action_matrix=sequential_opponent_actions[sequential_agent])
    elif sequential_agent == 'self_transition_down':
        return SelfTransition(id=sequential_agent, action_matrix=sequential_opponent_actions[sequential_agent])
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
    return agent




def main():
    # Initialize sequential agent
    sequential_agent = setup_sequential_agent(SEQUENTIAL_OPPONENTS, ACTION_MATRIX_LOOKUP)

    # Initialize tom agent
    #tom_agent = setup_sequential_agent(SEQUENTIAL_OPPONENTS, ACTION_MATRIX_LOOKUP) # TESTING
    # TODO set up actual tom agent
    api_key = os.getenv('OPENAI_API_KEY')
    model_id = 'player_0'
    model_settings = {
            "model": "gpt-3.5-turbo-1106",
            "max_tokens": 2000,
            "temperature": 0.2,
            "top_p": 1.0,
            "n": 1,
        }
    tom_agent = setup_tom_agent(api_key, model_id, model_settings, agent_type='hm', llm_type='gpt35')

    # Run game
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_episode(tom_agent, sequential_agent, num_rounds=50))



if __name__ == "__main__":
    main()