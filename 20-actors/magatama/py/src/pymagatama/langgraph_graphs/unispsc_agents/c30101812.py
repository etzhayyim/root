from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ZincChannelState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: ZincChannelState):
    errors = []
    if state['spec_data'].get('thickness', 0) < 1.0:
        errors.append('Thickness below threshold')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

graph = StateGraph(ZincChannelState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()