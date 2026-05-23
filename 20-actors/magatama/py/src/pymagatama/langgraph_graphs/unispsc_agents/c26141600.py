from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NuclearState(TypedDict):
    equipment_id: str
    export_license_status: bool
    shielding_audit: bool
    final_approval: bool

def check_compliance(state: NuclearState):
    state['export_license_status'] = True
    return 'check_compliance'

def audit_shielding(state: NuclearState):
    state['shielding_audit'] = True
    return 'audit_shielding'

graph = StateGraph(NuclearState)
graph.add_node('compliance', check_compliance)
graph.add_node('shielding', audit_shielding)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'shielding')
graph.add_edge('shielding', END)
app = graph.compile()
