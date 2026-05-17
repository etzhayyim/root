from typing import TypedDict
from langgraph.graph import StateGraph, END

class GrommetState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: GrommetState):
    required = ['material_composition', 'inner_diameter_mm']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specifications'}

def route_by_validation(state: GrommetState):
    return 'process' if state['validated'] else 'error'

graph = StateGraph(GrommetState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END, 'error': END})
app = graph.compile()