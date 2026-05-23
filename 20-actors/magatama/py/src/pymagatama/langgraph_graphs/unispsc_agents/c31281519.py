from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    part_specs: dict
    compliance_cleared: bool

def validate_nickel_alloy(state: ProcurementState):
    grade = state['part_specs'].get('grade')
    state['compliance_cleared'] = grade is not None
    return state

def check_dual_use(state: ProcurementState):
    # Business logic for export control checks
    return {'compliance_cleared': state['compliance_cleared']}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_nickel_alloy)
graph.add_node('export_check', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()
