from typing import TypedDict
from langgraph.graph import StateGraph, END

class DockRingState(TypedDict):
    load_capacity: float
    material: str
    compliance_report: str
    approved: bool

def validate_specs(state: DockRingState):
    if state['load_capacity'] < 500.0:
        return {'approved': False}
    return {'approved': True}

def update_compliance(state: DockRingState):
    return {'compliance_report': 'ISO-Certified'}

graph = StateGraph(DockRingState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', update_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph.compile()