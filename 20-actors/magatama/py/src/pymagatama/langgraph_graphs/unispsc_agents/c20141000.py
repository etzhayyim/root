from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    part_number: str
    specs: dict
    validation_passed: bool
    approval_workflow: List[str]

def validate_specs(state: ProcurementState):
    # Core logic for validating mechanical tolerance and material standards
    state['validation_passed'] = all(k in state['specs'] for k in ['material', 'tolerance'])
    return state

def route_procurement(state: ProcurementState):
    return 'approval' if state['validation_passed'] else END

def perform_approval(state: ProcurementState):
    state['approval_workflow'].append('Manager_Signoff')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('approval', perform_approval)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_procurement)
graph.add_edge('approval', END)
graph = graph.compile()
