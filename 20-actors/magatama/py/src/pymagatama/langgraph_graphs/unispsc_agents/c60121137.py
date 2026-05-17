from typing import TypedDict
from langgraph.graph import StateGraph, END

class AcrylicState(TypedDict):
    dimensions: tuple
    thickness: float
    has_safety_cert: bool

def validate_specs(state: AcrylicState) -> dict:
    is_valid = state['thickness'] > 0 and all(d > 0 for d in state['dimensions'])
    print(f'Validation result: {is_valid}')
    return {'is_valid': is_valid}

def process_procurement(state: AcrylicState) -> dict:
    return {'status': 'approved' if state.get('is_valid') else 'rejected'}

graph = StateGraph(AcrylicState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()