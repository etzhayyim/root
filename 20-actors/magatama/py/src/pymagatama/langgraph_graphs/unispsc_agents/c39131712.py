from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WiringDuctState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: WiringDuctState):
    errors = []
    if not state['spec_data'].get('Flame-Retardant Rating'):
        errors.append('Missing mandatory UL/CSA flame rating')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(WiringDuctState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()