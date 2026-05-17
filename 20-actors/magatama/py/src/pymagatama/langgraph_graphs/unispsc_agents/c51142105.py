from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    purity_level: float
    meets_standards: bool
    regulatory_approved: bool

def validate_chemical(state: ProcurementState):
    if state['purity_level'] >= 99.0:
        return {'meets_standards': True}
    return {'meets_standards': False}

def check_compliance(state: ProcurementState):
    return {'regulatory_approved': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_chemical)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()