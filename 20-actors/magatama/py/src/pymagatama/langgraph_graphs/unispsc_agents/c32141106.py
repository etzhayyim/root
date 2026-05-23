from typing import TypedDict
from langgraph.graph import StateGraph, END

class TubeBaseState(TypedDict):
    spec_data: dict
    validated: bool
    error_log: list

def validate_specs(state: TubeBaseState):
    required = ['Pin Configuration', 'Material Certification']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: TubeBaseState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(TubeBaseState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
