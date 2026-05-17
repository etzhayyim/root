from typing import TypedDict
from langgraph.graph import StateGraph, END

class DieState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: DieState):
    # Validate critical die mechanical properties
    required = ['bending_radius', 'material_grade']
    if all(k in state['spec_data'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specs'}

def process_die_order(state: DieState):
    return {'validated': True}

graph = StateGraph(DieState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_die_order)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')