from typing import TypedDict
from langgraph.graph import StateGraph, END

class StrainerState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_strainer_specs(state: StrainerState):
    required = ['micron_rating', 'material', 'pressure_rating']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing core specs'}

def check_compatibility(state: StrainerState):
    # Simulate logic check
    return {'validated': state['validated']}

graph = StateGraph(StrainerState)
graph.add_node('validate', validate_strainer_specs)
graph.add_node('compatibility', check_compatibility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compatibility')
graph.add_edge('compatibility', END)
graph = graph.compile()
