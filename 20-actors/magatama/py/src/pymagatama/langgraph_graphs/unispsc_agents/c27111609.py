from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WireStraightenerState(TypedDict):
    spec_params: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: WireStraightenerState):
    errors = []
    if state['spec_params'].get('max_diameter', 0) <= 0:
        errors.append('Invalid wire diameter range')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: WireStraightenerState):
    return 'success' if state['is_compliant'] else 'reject'

graph = StateGraph(WireStraightenerState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')