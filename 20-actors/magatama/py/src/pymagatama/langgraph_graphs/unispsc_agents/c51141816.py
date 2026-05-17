from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity: float
    safety_compliance: bool
    storage_method: str

def validate_purity(state: ChemicalProcurementState):
    if state['purity'] >= 99.0:
        return {'safety_compliance': True}
    return {'safety_compliance': False}

def route_by_compliance(state: ChemicalProcurementState):
    return 'process' if state['safety_compliance'] else 'reject'

graph = StateGraph(ChemicalProcurementState)
graph.add_node('validate', validate_purity)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance, {'process': END, 'reject': END})
graph.compile()