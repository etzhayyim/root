from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwitchState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: SwitchState):
    required = ['actuation_force_gram', 'switch_type']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required technical specs'}

def process_procurement(state: SwitchState):
    print('Processing adaptive switch procurement...')
    return {'validated': True}

graph = StateGraph(SwitchState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()