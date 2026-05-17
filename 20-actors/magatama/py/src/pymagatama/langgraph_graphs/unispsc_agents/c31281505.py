from typing import TypedDict
from langgraph.graph import StateGraph, END
class StampingState(TypedDict):
    spec_data: dict
    validation_results: dict
    is_approved: bool
def validate_specs(state: StampingState):
    specs = state.get('spec_data', {})
    valid = all(k in specs for k in ['alloy_grade', 'tolerance'])
    return {'validation_results': {'passed': valid}, 'is_approved': valid}
def check_compliance(state: StampingState):
    return 'approved' if state['is_approved'] else 'rejected'
graph = StateGraph(StampingState)
graph.add_node('validate', validate_specs)
graph.add_entry_point('validate')
graph.add_edge('validate', END)