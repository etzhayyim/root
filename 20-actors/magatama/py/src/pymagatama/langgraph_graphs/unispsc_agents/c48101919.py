from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    lid_specs: dict
    compliance_verified: bool
    final_approval: bool

def validate_compliance(state: ProcurementState):
    material = state['lid_specs'].get('material', '')
    return {'compliance_verified': material in ['PP', 'PET', 'Paper-FSC']}

def check_seal(state: ProcurementState):
    return {'final_approval': state['compliance_verified'] and state['lid_specs'].get('leak_proof', False)}

graph = StateGraph(ProcurementState)
graph.add_node('verify', validate_compliance)
graph.add_node('seal_check', check_seal)
graph.set_entry_point('verify')
graph.add_edge('verify', 'seal_check')
graph.add_edge('seal_check', END)
graph = graph.compile()