from typing import TypedDict
from langgraph.graph import StateGraph, END

class ComponentState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_specs(state: ComponentState):
    required = ['material', 'dimensions', 'tolerance']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required specs'}

def finalize_order(state: ComponentState):
    if state['validated']:
        print('Processing roll-formed component order')
    return state

graph = StateGraph(ComponentState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()