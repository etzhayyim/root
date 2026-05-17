from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    material_name: str
    chlorine_pct: float
    safety_verified: bool
    approved: bool

def validate_chemistry(state: ProcurementState):
    if state['chlorine_pct'] < 25.0:
        return {'approved': False}
    return {'approved': True}

def check_compliance(state: ProcurementState):
    if state['safety_verified']:
        return {'approved': state['approved']}
    return {'approved': False}

graph = StateGraph(ProcurementState)
graph.add_node('chemistry_check', validate_chemistry)
graph.add_node('compliance_check', check_compliance)
graph.add_edge('chemistry_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph.set_entry_point('chemistry_check')
graph = graph.compile()