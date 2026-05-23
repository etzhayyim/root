from typing import TypedDict
from langgraph.graph import StateGraph, END
class ForgingState(TypedDict):
    spec: dict
    inspection_status: str
    validation_passed: bool
def validate_specs(state: ForgingState):
    required = ['Material Grade', 'Dimensional Tolerance']
    passed = all(k in state['spec'] for k in required)
    return {'validation_passed': passed}
def check_quality(state: ForgingState):
    if state['validation_passed']:
        return {'inspection_status': 'COMPLETED'}
    return {'inspection_status': 'FAILED'}
graph = StateGraph(ForgingState)
graph.add_node('validate', validate_specs)
graph.add_node('inspection', check_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspection')
graph.add_edge('inspection', END)
graph = graph.compile()
