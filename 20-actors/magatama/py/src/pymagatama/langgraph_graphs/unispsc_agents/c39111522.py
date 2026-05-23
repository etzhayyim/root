from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: LightingState):
    required = ['Voltage rating', 'Certification (UL/PSE/CE)']
    errors = [f'Missing {f}' for f in required if f not in state['spec_data']]
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def finalize_order(state: LightingState):
    return {'approved': True}

graph = StateGraph(LightingState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
