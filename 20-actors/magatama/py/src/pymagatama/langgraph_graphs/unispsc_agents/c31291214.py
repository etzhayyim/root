from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    specs: dict
    validated: bool
    error_log: List[str]

def validate_specs(state: ExtrusionState):
    required = ['Material Grade', 'Dimensional Tolerance']
    missing = [f for f in required if f not in state['specs']]
    return {'validated': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: ExtrusionState):
    return 'valid' if state['validated'] else 'invalid'

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
