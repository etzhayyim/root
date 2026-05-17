from langgraph.graph import StateGraph, END
from typing import TypedDict, List
class DentalState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_errors: List[str]
def validate_specs(state: DentalState):
    errors = []
    if state['spec_data'].get('rpm', 0) > 30000: errors.append('Excessive RPM for safety')
    return {'is_compliant': len(errors) == 0, 'validation_errors': errors}
def finalize_procurement(state: DentalState):
    return {'is_compliant': True}
graph_builder = StateGraph(DentalState)
graph_builder.add_node('validate', validate_specs)
graph_builder.add_node('finalize', finalize_procurement)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'finalize')
graph_builder.add_edge('finalize', END)
graph = graph_builder.compile()