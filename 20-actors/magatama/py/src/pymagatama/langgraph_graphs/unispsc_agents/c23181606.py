from typing import TypedDict
from langgraph.graph import StateGraph, END

class LaserProcurementState(TypedDict):
    machine_id: str
    spec_verified: bool
    compliance_cleared: bool

def validate_specs(state: LaserProcurementState):
    print(f'Validating specs for {state[\'machine_id\']}')
    return {'spec_verified': True}

def check_export_compliance(state: LaserProcurementState):
    print('Checking dual-use compliance...')
    return {'compliance_cleared': True}

graph = StateGraph(LaserProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()