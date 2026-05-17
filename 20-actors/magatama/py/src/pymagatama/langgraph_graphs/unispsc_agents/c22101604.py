from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FittingState(TypedDict):
    specs: dict
    validated: bool
    error_log: List[str]

def validate_specs(state: FittingState):
    required = ['material', 'pressure_rating', 'thread_type']
    errors = [f'Missing {r}' for r in required if r not in state['specs']]
    return {'validated': len(errors) == 0, 'error_log': errors}

def route_by_validation(state: FittingState):
    return 'process' if state['validated'] else 'reject'

graph = StateGraph(FittingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'process': END, 'reject': END})

graph = graph.compile()