from typing import TypedDict
from langgraph.graph import StateGraph, END

class MatState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_safety_standards(state: MatState):
    required = ['flame_retardant', 'non_toxic']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def check_dimensions(state: MatState):
    print('Verifying dimensions for childcare safety compliance.')
    return state

graph = StateGraph(MatState)
graph.add_node('safety_check', validate_safety_standards)
graph.add_node('dim_check', check_dimensions)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'dim_check')
graph.add_edge('dim_check', END)
graph = graph.compile()