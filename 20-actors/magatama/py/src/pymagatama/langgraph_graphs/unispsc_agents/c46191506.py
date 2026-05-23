from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FlameArrestorState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: FlameArrestorState):
    errors = []
    if 'pressure_rating' not in state['spec_data']:
        errors.append('Missing pressure rating')
    if 'certification' not in state['spec_data']:
        errors.append('Missing ISO 16852 certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: FlameArrestorState):
    return 'compliant' if state['is_compliant'] else 'flag_for_review'

graph = StateGraph(FlameArrestorState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
