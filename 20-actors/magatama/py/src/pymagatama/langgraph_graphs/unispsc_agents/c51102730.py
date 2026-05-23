from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalProcurementState(TypedDict):
    purity: float
    safety_clearance: bool
    compliant: bool

def validate_safety(state: ChemicalProcurementState):
    state['compliant'] = state['purity'] >= 99.0 and state['safety_clearance']
    return state

workflow = StateGraph(ChemicalProcurementState)
workflow.add_node('safety_check', validate_safety)
workflow.set_entry_point('safety_check')
workflow.add_edge('safety_check', END)
graph = workflow.compile()
