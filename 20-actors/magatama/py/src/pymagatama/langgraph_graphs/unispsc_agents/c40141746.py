from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SightGlassState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_pressure_rating(state: SightGlassState):
    rating = state['spec_data'].get('pressure_rating', 0)
    if rating <= 0:
        state['validation_errors'].append('Invalid pressure rating.')
    return {'validation_errors': state['validation_errors']}

def check_compliance(state: SightGlassState):
    state['is_compliant'] = len(state['validation_errors']) == 0
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(SightGlassState)
graph.add_node('validate_specs', validate_pressure_rating)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()