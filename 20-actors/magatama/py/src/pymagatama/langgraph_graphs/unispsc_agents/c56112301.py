from typing import TypedDict
from langgraph.graph import StateGraph, END
class BackRestState(TypedDict):
    spec_data: dict
    approved: bool
    validation_errors: list
def validate_ergonomic_specs(state: BackRestState):
    errors = []
    if state['spec_data'].get('adjustability_range', 0) < 5:
        errors.append('Adjustability range below ergonomic standard.')
    return {'validation_errors': errors, 'approved': len(errors) == 0}
def safety_compliance_check(state: BackRestState):
    if not state['spec_data'].get('flame_retardant', False):
        state['validation_errors'].append('Missing flame retardancy certificate.')
        state['approved'] = False
    return state
graph = StateGraph(BackRestState)
graph.add_node('validate_ergonomics', validate_ergonomic_specs)
graph.add_node('compliance_review', safety_compliance_check)
graph.set_entry_point('validate_ergonomics')
graph.add_edge('validate_ergonomics', 'compliance_review')
graph.add_edge('compliance_review', END)
graph = graph.compile()