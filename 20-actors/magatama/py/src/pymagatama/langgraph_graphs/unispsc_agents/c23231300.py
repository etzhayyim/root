from typing import TypedDict, List
from langgraph.graph import StateGraph

class PressMachineState(TypedDict):
    machine_id: str
    specifications: dict
    compliance_validated: bool
    approved: bool

def validate_specs(state: PressMachineState):
    # Simulate CAD/spec validation for industrial press
    specs = state.get('specifications', {})
    valid = 'pressure_capacity_tons' in specs and 'safety_certification_ce_iso' in specs
    return {'compliance_validated': valid}

def approval_check(state: PressMachineState):
    return {'approved': state['compliance_validated']}

graph = StateGraph(PressMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', 'END')
graph = graph.compile()