from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ExtrusionState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ExtrusionState):
    errors = []
    if 'tolerance' not in state['spec_data']:
        errors.append('Missing tolerance specification')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def route_by_spec(state: ExtrusionState):
    return 'process' if state['approved'] else END

graph = StateGraph(ExtrusionState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()