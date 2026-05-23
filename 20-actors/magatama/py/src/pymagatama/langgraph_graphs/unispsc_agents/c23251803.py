from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DieCastingState(TypedDict):
    die_id: str
    specs: dict
    validation_passed: bool
    approver: str

def validate_specs(state: DieCastingState):
    # Simulate CAD and material spec validation
    required_fields = ['material', 'tolerance', 'life_cycle']
    state['validation_passed'] = all(k in state['specs'] for k in required_fields)
    return state

def route_by_validation(state: DieCastingState):
    return 'approve' if state['validation_passed'] else 'reject'

graph = StateGraph(DieCastingState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
