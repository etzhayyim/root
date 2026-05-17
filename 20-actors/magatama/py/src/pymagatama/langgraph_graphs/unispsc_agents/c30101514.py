from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_specs: dict
    compliance_ok: bool
    final_approval: bool

def validate_lead_specs(state: ProcurementState):
    purity = state['material_specs'].get('lead_purity_percentage', 0)
    return {'compliance_ok': purity >= 99.9}

def route_by_compliance(state: ProcurementState):
    return 'approve' if state['compliance_ok'] else END

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_lead_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()