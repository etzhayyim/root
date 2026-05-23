from typing import TypedDict
from langgraph.graph import StateGraph, END
class BrassCastState(TypedDict):
    spec_sheet: dict
    validation_passed: bool
def validate_specs(state: BrassCastState):
    required = ['alloy', 'tolerance', 'surface_finish']
    passed = all(k in state['spec_sheet'] for k in required)
    return {'validation_passed': passed}
def check_compliance(state: BrassCastState):
    return 'approved' if state['validation_passed'] else 'rejected'
graph = StateGraph(BrassCastState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
