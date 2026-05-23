from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DepthGaugeState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: DepthGaugeState):
    errors = []
    if state['spec_data'].get('range', 0) <= 0:
        errors.append('Invalid measurement range')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: DepthGaugeState):
    return 'valid' if state['is_compliant'] else 'invalid'

graph = StateGraph(DepthGaugeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph.compile()
