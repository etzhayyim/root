from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    instrument_id: str
    compliance_checks: dict
    is_approved: bool

def validate_sterilization(state: ProcurementState):
    state['compliance_checks']['sterilization'] = True
    return state

def check_depth_specs(state: ProcurementState):
    state['compliance_checks']['depth_accuracy'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate_sterilization', validate_sterilization)
graph.add_node('check_depth_specs', check_depth_specs)
graph.add_edge('validate_sterilization', 'check_depth_specs')
graph.add_edge('check_depth_specs', END)
graph.set_entry_point('validate_sterilization')
graph = graph.compile()